import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from utils.logger import get_logger
from utils.config import settings
from core.pdf_parser import TextElement

logger = get_logger(__name__)


class StockInfo(BaseModel):
    """在庫情報"""

    carryover: Optional[int] = Field(None, description="繰越在庫")
    incoming: Optional[int] = Field(None, description="入庫数")
    w_value: Optional[int] = Field(None, description="W値")
    outgoing: Optional[int] = Field(None, description="出庫数")
    remaining: Optional[int] = Field(None, description="在庫残高")
    total: Optional[int] = Field(None, description="合計")
    unit_price: Optional[int] = Field(None, description="単価")


class QuantityInfo(BaseModel):
    """数量情報"""

    quantity: Optional[int] = Field(None, description="数量")
    unit_price: Optional[int] = Field(None, description="単価")


class EntryDetail(BaseModel):
    """明細行情報"""

    no: str = Field(..., description="明細番号")
    description: str = Field(..., description="摘要")
    tax_rate: str = Field(..., description="税率")
    amount: str = Field(..., description="金額")
    stock_info: Optional[StockInfo] = Field(None, description="在庫情報")
    quantity_info: Optional[QuantityInfo] = Field(None, description="数量情報")
    date_range: Optional[str] = Field(None, description="日付範囲")
    page_no: int = Field(..., description="ページ番号")


class CustomerEntry(BaseModel):
    """顧客情報"""

    customer_code: str = Field(..., description="顧客コード")
    customer_name: str = Field(..., description="顧客名")
    department: Optional[str] = Field(None, description="部署名")
    box_number: Optional[str] = Field(None, description="文書箱番号")
    entries: List[EntryDetail] = Field(default_factory=list, description="明細行リスト")


class DocumentStructure(BaseModel):
    """請求書全体の構造"""

    pdf_filename: str = Field(..., description="PDFファイル名")
    total_amount: str = Field(..., description="合計金額")
    customers: List[CustomerEntry] = Field(
        default_factory=list, description="顧客情報リスト"
    )


class StructuringEngine:
    """テキストを構造化するエンジン"""

    def __init__(self):
        # Azure OpenAI APIの設定
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    async def structure_invoice(
        self, text_elements: Dict[int, List[TextElement]]
    ) -> DocumentStructure:
        """
        請求書のテキストを構造化する

        Args:
            text_elements (Dict[int, List[TextElement]]): ページ毎のテキスト要素リスト

        Returns:
            DocumentStructure: 構造化されたデータ
        """
        try:
            # テキスト要素の前処理
            processed_text = self._preprocess_text(text_elements)

            # Azure OpenAI APIを使用して構造化
            structured_data = await self._call_openai_api(processed_text)

            # 構造化データの検証
            result = DocumentStructure.parse_obj(structured_data)
            logger.info("構造化処理が完了")
            return result

        except Exception as e:
            logger.error(f"構造化処理でエラー: {e}", exc_info=True)
            raise

    def _preprocess_text(self, text_elements: Dict[int, List[TextElement]]) -> str:
        """
        テキスト要素を前処理する

        Args:
            text_elements (Dict[int, List[TextElement]]): ページ毎のテキスト要素リスト

        Returns:
            str: 前処理済みのテキスト
        """
        processed_text = []

        for page_num, elements in sorted(text_elements.items()):
            # ページ区切りの追加
            if processed_text:
                processed_text.append("\n=== ページ区切り ===\n")

            # テキスト要素の追加（位置情報付き）
            for element in elements:
                text = element.text.strip()
                if text:
                    position = f"[x:{element.x0:.1f},y:{element.y0:.1f}]"
                    font_info = ""
                    if element.font_name or element.font_size:
                        font_info = (
                            f"[font:{element.font_name},size:{element.font_size:.1f}]"
                        )
                    processed_text.append(f"{position}{font_info} {text}")

        return "\n".join(processed_text)

    async def _call_openai_api(self, text: str) -> Dict:
        """
        Azure OpenAI APIを呼び出して構造化を実行する

        Args:
            text (str): 構造化対象のテキスト

        Returns:
            Dict: 構造化されたデータ
        """
        from openai import AsyncAzureOpenAI

        try:
            client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )

            # システムプロンプトの構築
            system_prompt = """
請求書のテキストから顧客情報と明細を抽出し、構造化データとして出力してください。
以下の重要な処理ルールに従ってください：

0. 文書全体の情報抽出：
   - 文書全体のPDFファイル名を使用
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

            # APIの呼び出しとレスポンスの取得
            completion = await client.beta.chat.completions.parse(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": self._build_prompt(text)},
                ],
                response_format=DocumentStructure,
            )

            logger.info("APIレスポンスを受信")
            return completion.choices[0].message.parsed

        except Exception as e:
            logger.error(f"OpenAI APIの呼び出しでエラー: {e}", exc_info=True)
            raise

    def _build_prompt(self, text: str) -> str:
        """
        プロンプトを構築する

        Args:
            text (str): 構造化対象のテキスト

        Returns:
            str: 構築されたプロンプト
        """
        return f"""
以下の請求書テキストをJSON形式に構造化してください。

テキスト:
{text}

出力形式:
{{
    "pdf_filename": "ファイル名",
    "total_amount": "合計金額",
    "customers": [
        {{
            "customer_code": "顧客コード",
            "customer_name": "顧客名",
            "department": "部署名",
            "box_number": "文書箱番号",
            "entries": [
                {{
                    "no": "明細番号",
                    "description": "摘要",
                    "tax_rate": "税率",
                    "amount": "金額",
                    "stock_info": {{
                        "carryover": null,
                        "incoming": null,
                        "w_value": null,
                        "outgoing": null,
                        "remaining": null,
                        "total": null,
                        "unit_price": null
                    }},
                    "quantity_info": {{
                        "quantity": null,
                        "unit_price": null
                    }},
                    "date_range": "日付範囲",
                    "page_no": 1
                }}
            ]
        }}
    ]
}}

注意事項:
1. 位置情報とフォント情報は構造化の参考にしてください
2. 数値は文字列として出力してください
3. 日付は YYYY/MM/DD 形式で出力してください
4. 在庫情報と数量情報は該当する場合のみ出力してください
"""


# 使用例:
"""
engine = StructuringEngine()

# 構造化処理
structured_data = await engine.structure_invoice(text_elements)

# 結果の確認
print(json.dumps(structured_data.dict(), indent=2, ensure_ascii=False))
"""
