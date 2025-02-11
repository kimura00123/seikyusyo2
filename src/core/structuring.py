import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from utils.logger import get_logger
from utils.config import Config
from core.pdf_parser import TextElement

logger = get_logger(__name__)


class StockInfo(BaseModel):
    """在庫情報"""

    carryover: int = Field(0, description="繰越在庫")
    incoming: int = Field(0, description="入庫数")
    w_value: int = Field(0, description="W値")
    outgoing: int = Field(0, description="出庫数")
    remaining: int = Field(0, description="在庫残高")
    total: int = Field(0, description="合計")
    unit_price: int = Field(0, description="単価")


class QuantityInfo(BaseModel):
    """数量情報"""

    quantity: int = Field(0, description="数量")
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
    department: str = Field("", description="部署名")
    box_number: str = Field("", description="文書箱番号")
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
        self.api_key = Config.AZURE_OPENAI_API_KEY
        self.endpoint = Config.AZURE_OPENAI_ENDPOINT
        self.api_version = Config.AZURE_OPENAI_API_VERSION
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME

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
        try:
            from openai import AsyncAzureOpenAI

            client = AsyncAzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
            )

            # プロンプトの構築
            prompt = self._build_prompt(text)

            # APIの呼び出し
            response = await client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "請求書のテキストをJSON形式に構造化してください。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            # レスポンスのパース
            result = json.loads(response.choices[0].message.content)
            return result

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
                        "carryover": 0,
                        "incoming": 0,
                        "w_value": 0,
                        "outgoing": 0,
                        "remaining": 0,
                        "total": 0,
                        "unit_price": 0
                    }},
                    "quantity_info": {{
                        "quantity": 0,
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
