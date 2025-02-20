import os
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from .pdf_parser import TextElement


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
    amount: str
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
    total_amount: str
    customers: List[CustomerEntry]


class StructuringEngine:
    def __init__(self, pdf_path: str):
        """構造化エンジンの初期化"""
        from openai import AzureOpenAI
        from src.utils.config import settings

        self.pdf_path = pdf_path
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )

    def structure_invoice(
        self, text_elements: Dict[int, List[TextElement]]
    ) -> DocumentStructure:
        """テキスト要素を構造化データに変換する"""
        # テキストを1つの文字列に結合
        text = self._combine_text_elements(text_elements)
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
       - 明細の基本情報（明細番号、摘要、消費税率、金額）を抽出
       - 各明細に関連する追加情報（日付範囲、在庫情報、数量情報）も漏れなく抽出
       - 明細行の後に続く補足情報（時間指定なし、配送先住所等）は適切に処理
       - 各明細にページ番号（page_no）を付与

    4. データ形式：
       - 顧客コード: 'F'で始まる形式で抽出 (例: F034)
       - 会社名と部署:
            - 会社名は「株式会社」「㈱」で終わる部分
            - 残りを部署として扱う
       - 金額: ¥マークを付けて表示
       - 日付: 元の形式を保持 (例: 2024/08月分(2024/08/01 - 2024/08/31))
       - 数量情報と在庫情報は別々のオブジェクトとして管理

    処理の注意点：
    - ヘッダー情報（"寺田倉庫株式会社"や住所情報など）は無視する
    - テーブルのカラムヘッダー行（|No|摘 要|消費税率|金 額|）は無視する
    - 改ページマーカー（-----）は無視する
    - 同じ顧客の明細は、ページをまたいでも一つの配列にまとめる
    """

            from src.utils.config import settings

            completion = self.client.beta.chat.completions.parse(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0,
                response_format=DocumentStructure,
            )

            return completion.choices[0].message.parsed
        except Exception as e:
            from src.utils.logger import get_logger

            logger = get_logger(__name__)
            logger.error(f"構造化データの変換に失敗: {e}")
            raise

    def _combine_text_elements(
        self, text_elements: Dict[int, List[TextElement]]
    ) -> str:
        """テキスト要素を1つの文字列に結合する"""
        combined_text = []
        for page_num in sorted(text_elements.keys()):
            combined_text.append(f"\n=== ページ {page_num} ===\n")
            # Y座標の降順（上から下）でソート
            elements = sorted(text_elements[page_num], key=lambda x: -x.y0)
            for element in elements:
                combined_text.append(element.text)
        return "\n".join(combined_text)
