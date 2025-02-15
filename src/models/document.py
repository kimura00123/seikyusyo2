from typing import List, Optional
from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    """在庫情報モデル"""

    carryover: int = Field(..., description="繰越在庫")
    incoming: int = Field(..., description="入庫数")
    w_value: int = Field(..., description="W値")
    outgoing: int = Field(..., description="出庫数")
    remaining: int = Field(..., description="在庫残高")
    total: int = Field(..., description="合計")
    unit_price: int = Field(..., description="単価")


class QuantityInfo(BaseModel):
    """数量情報モデル"""

    quantity: int = Field(..., description="数量")
    unit_price: Optional[int] = Field(None, description="単価")


class EntryDetail(BaseModel):
    """明細行モデル"""

    no: str = Field(..., description="明細番号")
    description: str = Field(..., description="明細内容")
    tax_rate: str = Field(..., description="税率")
    amount: str = Field(..., description="金額")
    stock_info: Optional[StockInfo] = Field(None, description="在庫情報")
    quantity_info: Optional[QuantityInfo] = Field(None, description="数量情報")
    date_range: Optional[str] = Field(None, description="日付範囲")
    page_no: int = Field(..., description="ページ番号")


class CustomerEntry(BaseModel):
    """顧客情報モデル"""

    customer_code: str = Field(..., description="顧客コード")
    customer_name: str = Field(..., description="顧客名")
    department: str = Field(..., description="部署")
    box_number: str = Field(..., description="ボックス番号")
    entries: List[EntryDetail] = Field(default_factory=list, description="明細行リスト")


class DocumentStructure(BaseModel):
    """請求書構造化データモデル"""

    pdf_filename: str = Field(..., description="PDFファイル名")
    total_amount: str = Field(..., description="合計金額")
    customers: List[CustomerEntry] = Field(
        default_factory=list, description="顧客情報リスト"
    )
