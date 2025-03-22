import os
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from src.utils.config import get_settings
from src.core.image_processor import ImageProcessor
from src.utils.temp_manager import temp_manager
from src.utils.logger import get_logger
from src.utils.text_processing import preprocess_text_for_detail_numbers, is_detail_number

logger = get_logger(__name__)


class StockInfo(BaseModel):
    carryover: int
    incoming: int
    w_value: int
    outgoing: int
    remaining: int
    total: int
    unit_price: int


class QuantityInfo(BaseModel):
    quantity: int
    unit_price: Optional[int] = None


class EntryDetail(BaseModel):
    no: str
    description: str
    tax_rate: str
    amount: int
    stock_info: Optional[StockInfo] = None
    quantity_info: Optional[QuantityInfo] = None
    date_range: Optional[str] = None
    page_no: int


class CustomerEntry(BaseModel):
    customer_code: str
    customer_name: str
    department: str
    box_number: str
    entries: List[EntryDetail]


class DocumentStructure(BaseModel):
    pdf_filename: str
    total_amount: int
    customers: List[CustomerEntry]


class StructuringEngine:
    def __init__(self, pdf_path: str, task_id: str):
        """構造化エンジンの初期化"""
        from openai import AzureOpenAI
        from src.utils.config import get_settings

        self.pdf_path = pdf_path
        self.task_id = task_id
        self.client = AzureOpenAI(
            api_key=get_settings().AZURE_OPENAI_API_KEY,
            api_version=get_settings().AZURE_OPENAI_API_VERSION,
            azure_endpoint=get_settings().AZURE_OPENAI_ENDPOINT,
        )

    def _preprocess_text_for_llm(self, text: str) -> str:
        """
        LLMに渡す前にテキストを前処理する
        特定の文字列を削除または置換する
        
        Args:
            text: 前処理するテキスト
            
        Returns:
            前処理されたテキスト
        """
        # 削除または置換する文字列のリスト
        # 将来的に他の文字列も追加できるようにリストで管理
        replacements = [
            ("（単体）", ""),  # 全角括弧の「単体」を削除
            ("(単体)", ""),    # 半角括弧の「単体」を削除
        ]
        
        # 各置換処理を適用
        processed_text = text
        for target, replacement in replacements:
            processed_text = processed_text.replace(target, replacement)
        
        logger.debug(f"テキスト前処理を実行: {len(replacements)}個の置換パターンを適用")
        return processed_text

    def calculate_approximate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> Any:
        """
        Azure OpenAI API の利用料金の概算を計算します。

        Args:
            model_name: 使用するモデル名 (例: "gpt-4o-2024-08-06")。
            prompt_tokens: プロンプトトークン数。
            completion_tokens: 補完トークン数。

        Returns:
            概算料金 (日本円)。モデル情報がない場合はエラーメッセージ。
        """
        # モデルごとの料金 (100万トークンあたり、日本円)
        # 入力トークン100万トークンあたり$2.5 = 375円
        # 出力トークン100万トークン当たり$10 = 1500円
        # 1＄は150円として計算
        model_prices = {
            "gpt4o-japaneast": {"input": 375.0, "output": 1500.0},
            "o3-mini": {"input": 165.0, "output": 660.0},
            "gpt-4o-mini": {"input": 375.0, "output": 1500.0},
            # 他のモデルの料金もここに追加可能
        }

        # モデル名が登録されていない場合はデフォルト値を使用
        if model_name not in model_prices:
            logger.warning(f"モデル '{model_name}' の料金情報が見つかりません。デフォルト値を使用します。")
            # 文字列ではなく数値を返すように修正
            return 0.0

        input_cost_per_token = model_prices[model_name]["input"] / 1000000
        output_cost_per_token = model_prices[model_name]["output"] / 1000000

        total_cost = (prompt_tokens * input_cost_per_token) + (completion_tokens * output_cost_per_token)

        return total_cost

    def reset_processing_state(self):
        """
        処理状態をリセットする
        新しいPDFファイルの処理を開始する前に呼び出す
        """
        logger.info("処理状態をリセットします")
        # 内部状態の初期化
        self._cached_data = None
        self._previous_results = None
        # その他必要なリセット処理があれば追加

    def structure_invoice(self, text_content: str) -> DocumentStructure:
        """テキスト要素を構造化データに変換する（改善版）"""
        # グローバルのloggerを使用
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        
        # 処理開始時に状態をリセット
        self.reset_processing_state()
        
        # テキストを前処理
        text = self._preprocess_text_for_llm(text_content)
        
        # オリジナルのファイル名を取得
        pdf_filename = temp_manager.get_original_filename(self.task_id)
        
        # Azure OpenAI APIにプロンプトを送信
        try:
            system_prompt = f"""
請求書のテキストから顧客情報と明細を抽出し、構造化データとして出力してください。
対象のPDFファイル名は "{pdf_filename}" です。
以下の重要な処理ルールに従ってください：

0. 文書全体の情報抽出：
   - 文書全体のPDFファイル名："{pdf_filename}" を使用
   - 文書全体の請求合計額：必ず「ご請求合計額」または「ご請求金額合計」の後に続く実際の金額を数値のみで抽出すること。サンプル値ではなく実際の値（例：999999）を抽出すること。
   - これらの情報はDocumentStructureレベルで保持する

1. 改ページ処理の考慮：
   - 各ページにはヘッダー情報（寺田倉庫株式会社、住所等）が含まれる可能性がある
   - ページをまたぐ顧客情報は、同じ顧客コードと文書箱番号で関連付けを行う
   - ヘッダー情報を含む行は無視し、実際の明細データのみを抽出
   - ヘッダー情報（寺田倉庫株式会社...）の出現でページ番号をインクリメント
   - 各明細のpage_noフィールドに、その明細が出現したページ番号を記録

2. 顧客情報の継続性：
   - 顧客コード（例：F034）が出現した後、次の顧客コードが出現するまでの全ての明細はその顧客に属する
   - 改ページによってヘッダーが挿入されても、顧客情報の連続性は維持する
   - 前のページの顧客に関する明細は、ヘッダーをまたいでも同じ顧客の明細として処理する

3. 明細の抽出ルール：
   - 明細番号（No）は必ず1から始まり、連続性を保っています。最後の明細まで漏れなく連続値で抽出すること
   - 明細の最終行後に出現する「以下余白」または、「合計」「小計」など文字列が出現するまですべての明細を必ず抽出すること
   - 同じ会社名が複数回出現する場合でも、それぞれを別の明細として正確に抽出する
   - 明細の基本情報（明細番号、摘要、消費税率、金額）を抽出
   - 各明細に関連する追加情報（日付範囲、在庫情報、数量情報）も漏れなく抽出
   - 明細行の後に続く補足情報（時間指定なし、配送先住所等）は適切に処理
   - 各明細にページ番号（page_no）を付与

4. データ形式：
    - 顧客コード: 明細の摘要欄から'F'または'S'で始まるコード(例: F245, S414)を抽出すること。万一F,Sで始まるコードがない場合には、顧客名にく括弧内の数字(例: (00353540116))などを抽出して顧客コードとする。ヘッダーの「お客様番号」とは区別すること。   
        - 会社名は「株式会社」「㈱」で終わる部分
        - 残りを部署として扱う
   - 金額: 数値のみを抽出（¥記号やカンマは除去）
   - 数量: 数値のみを抽出（カンマは除去）
   - 日付: 元の形式を保持 (例: 2024/08月分(2024/08/01 - 2024/08/31))
   - 数量情報と在庫情報は別々のオブジェクトとして管理

処理の注意点：
- ヘッダー情報（"寺田倉庫株式会社"や住所情報など）は無視する
- テーブルのカラムヘッダー行（|No|摘 要|消費税率|金 額|）は無視する
- 改ページマーカー（-----）は無視する
- 同じ顧客の明細は、ページをまたいでも一つの配列にまとめる

特に重要:
- 金額や数量の値は必ず数値のみを抽出する。¥記号やカンマ(,)など、数字以外の文字は全て取り除くこと。
- 例: "¥1,234" → 1234, "10,000個" → 10000
"""
            from src.utils.config import get_settings

            completion = self.client.beta.chat.completions.parse(
                model=get_settings().AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format=DocumentStructure,
            )

            document = completion.choices[0].message.parsed
            
            # トークン使用量の取得とログ記録
            usage = completion.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # モデル名を取得
            model_name = get_settings().AZURE_OPENAI_DEPLOYMENT_NAME
            
            # 概算料金を計算
            approximate_cost = self.calculate_approximate_cost(model_name, prompt_tokens, completion_tokens)
            
            # トークン使用量と料金をログに記録
            logger.info(f"トークン使用量: 入力={prompt_tokens}, 出力={completion_tokens}, 合計={total_tokens}")
            logger.info(f"概算料金: ¥{approximate_cost:.2f} (モデル: {model_name})")
            
            # 構造化データの後処理（数値の整形）
            document = self._post_process_document(document)
            
            # 構造化完了後、明細画像を抽出
            self._extract_detail_images(document)
            
            return document
        except Exception as e:
            logger.error(f"構造化データの変換に失敗: {e}")
            raise

    def _post_process_document(self, document: DocumentStructure) -> DocumentStructure:
        """構造化データの後処理を行う"""
        def clean_numeric_value(value: Any) -> int:
            """金額や数量の文字列から数値のみを抽出する"""
            if value is None:
                return 0
                
            if isinstance(value, int):
                return value
                
            if not isinstance(value, str):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
                    
            # ¥記号、カンマ、空白などを削除
            clean_value = re.sub(r'[¥,\s]', '', value)
            # 数値のみを抽出
            match = re.search(r'\d+', clean_value)
            if match:
                return int(match.group())
            return 0
        
        # 全体の合計金額を数値に変換
        document.total_amount = clean_numeric_value(document.total_amount)
        
        for customer in document.customers:
            for entry in customer.entries:
                # 金額を数値に変換
                entry.amount = clean_numeric_value(entry.amount)
                
                # 在庫情報がある場合は各フィールドを数値に変換
                if entry.stock_info:
                    entry.stock_info.carryover = clean_numeric_value(entry.stock_info.carryover)
                    entry.stock_info.incoming = clean_numeric_value(entry.stock_info.incoming)
                    entry.stock_info.w_value = clean_numeric_value(entry.stock_info.w_value)
                    entry.stock_info.outgoing = clean_numeric_value(entry.stock_info.outgoing)
                    entry.stock_info.remaining = clean_numeric_value(entry.stock_info.remaining)
                    entry.stock_info.total = clean_numeric_value(entry.stock_info.total)
                    entry.stock_info.unit_price = clean_numeric_value(entry.stock_info.unit_price)
                
                # 数量情報がある場合は各フィールドを数値に変換
                if entry.quantity_info:
                    entry.quantity_info.quantity = clean_numeric_value(entry.quantity_info.quantity)
                    if entry.quantity_info.unit_price is not None:
                        entry.quantity_info.unit_price = clean_numeric_value(entry.quantity_info.unit_price)
        
        return document

    def _extract_detail_images(self, document: DocumentStructure) -> None:
        """構造化データから明細画像を抽出する"""
        try:
            processor = ImageProcessor()
            try:
                # 全明細の位置情報を一度だけ抽出
                regions = processor.extract_detail_regions(self.pdf_path)
                
                # 各明細の画像を抽出して保存
                for customer in document.customers:
                    for entry in customer.entries:
                        image_path = temp_manager.get_image_path(self.task_id, entry.no)
                        if not os.path.exists(image_path):
                            region = next(
                                (r for r in regions if r.no == entry.no),
                                None
                            )
                            if region:
                                processor.extract_single_detail_image(
                                    self.pdf_path,
                                    region,
                                    image_path
                                )
                            else:
                                logger.warning(f"明細番号 {entry.no} の位置情報が見つかりません")
            finally:
                # 必ずキャッシュをクリーンアップ
                processor.cleanup()

        except Exception as e:
            logger.error(f"明細画像の抽出に失敗: {e}")
            raise