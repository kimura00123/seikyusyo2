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
    def __init__(self):
        pass

    def structure_invoice(
        self, text_elements: Dict[int, List[TextElement]]
    ) -> DocumentStructure:
        """テキスト要素を構造化データに変換する"""
        # デモ用の仮実装
        return DocumentStructure(
            pdf_filename="example.pdf",
            total_amount="100,000",
            customers=[
                CustomerEntry(
                    customer_code="C001",
                    customer_name="株式会社テスト",
                    department="営業部",
                    box_number="123",
                    entries=[
                        EntryDetail(
                            no="1",
                            description="商品A",
                            tax_rate="10%",
                            amount="50,000",
                            date_range="2025/01/01-2025/01/31",
                            page_no=1,
                            stock_info=StockInfo(
                                carryover=100,
                                incoming=50,
                                w_value=30,
                                outgoing=20,
                                remaining=130,
                                total=150,
                                unit_price=1000,
                            ),
                            quantity_info=QuantityInfo(
                                quantity=50,
                                unit_price=1000,
                            ),
                        ),
                        EntryDetail(
                            no="2",
                            description="商品B",
                            tax_rate="8%",
                            amount="50,000",
                            date_range="2025/01/01-2025/01/31",
                            page_no=1,
                            stock_info=StockInfo(
                                carryover=200,
                                incoming=100,
                                w_value=60,
                                outgoing=40,
                                remaining=260,
                                total=300,
                                unit_price=2000,
                            ),
                            quantity_info=QuantityInfo(
                                quantity=25,
                                unit_price=2000,
                            ),
                        ),
                    ],
                )
            ],
        )
