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

    def structure_invoice(
        self, text_content: str
    ) -> DocumentStructure:
        """テキスト要素を構造化データに変換する（改善版）"""
        # テキストを直接使用
        text = text_content

        pdf_filename = os.path.basename(self.pdf_path)

        # Azure OpenAI APIにプロンプトを送信
        try:
            system_prompt = f"""
    請求書のテキストから顧客情報と明細を抽出し、構造化データとして出力してください。
    対象のPDFファイル名は "{pdf_filename}" です。
    以下の重要な処理ルールに従ってください：

    0. 文書全体の情報抽出：
       - 文書全体のPDFファイル名："{pdf_filename}" を使用
       - 文書全体の請求合計額：「ご請求合計額」の後に続く金額（例：¥682,559）を抽出
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
       - 明細番号（No）は連続性を保つ
       - 欠番がある場合も、実際に見つかった番号を使用する（連番を強制しない）
       - 明細の基本情報（明細番号、摘要、消費税率、金額）を抽出
       - 各明細に関連する追加情報（日付範囲、在庫情報、数量情報）も漏れなく抽出
       - 明細行の後に続く補足情報（時間指定なし、配送先住所等）は適切に処理
       - 各明細にページ番号（page_no）を付与

    4. データ形式：
       - 顧客コード: 'F'で始まる形式で抽出 (例: F034)
       - 会社名と部署:
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
            
            # 構造化データの後処理（数値の整形）
            # document = self._post_process_document(document)
            
            # 構造化完了後、明細画像を抽出
            self._extract_detail_images(document)
            
            return document
        except Exception as e:
            from src.utils.logger import get_logger

            logger = get_logger(__name__)
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