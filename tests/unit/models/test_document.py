"""
請求書構造化データモデルのテスト
"""

import pytest
from pydantic import ValidationError

from src.models.document import (
    StockInfo,
    QuantityInfo,
    EntryDetail,
    CustomerEntry,
    DocumentStructure,
)


def test_stock_info_creation():
    """StockInfoモデルの作成テスト"""
    stock_data = {
        "carryover": 100,
        "incoming": 50,
        "w_value": 30,
        "outgoing": 20,
        "remaining": 130,
        "total": 180,
        "unit_price": 1000,
    }
    stock = StockInfo(**stock_data)
    assert stock.carryover == 100
    assert stock.incoming == 50
    assert stock.w_value == 30
    assert stock.outgoing == 20
    assert stock.remaining == 130
    assert stock.total == 180
    assert stock.unit_price == 1000


def test_stock_info_validation():
    """StockInfoモデルのバリデーションテスト"""
    with pytest.raises(ValidationError):
        StockInfo(
            carryover="invalid",  # 数値であるべき
            incoming=50,
            w_value=30,
            outgoing=20,
            remaining=130,
            total=180,
            unit_price=1000,
        )


def test_quantity_info_creation():
    """QuantityInfoモデルの作成テスト"""
    # 必須フィールドのみ
    quantity = QuantityInfo(quantity=100)
    assert quantity.quantity == 100
    assert quantity.unit_price is None

    # オプショナルフィールドあり
    quantity_with_price = QuantityInfo(quantity=100, unit_price=1000)
    assert quantity_with_price.quantity == 100
    assert quantity_with_price.unit_price == 1000


def test_entry_detail_creation():
    """EntryDetailモデルの作成テスト"""
    entry_data = {
        "no": "001",
        "description": "テスト商品",
        "tax_rate": "10%",
        "amount": "¥1,000",
        "page_no": 1,
    }
    entry = EntryDetail(**entry_data)
    assert entry.no == "001"
    assert entry.description == "テスト商品"
    assert entry.tax_rate == "10%"
    assert entry.amount == "¥1,000"
    assert entry.page_no == 1
    assert entry.stock_info is None
    assert entry.quantity_info is None
    assert entry.date_range is None


def test_entry_detail_with_optional_fields():
    """EntryDetailモデルのオプショナルフィールドテスト"""
    stock_info = StockInfo(
        carryover=100,
        incoming=50,
        w_value=30,
        outgoing=20,
        remaining=130,
        total=180,
        unit_price=1000,
    )
    quantity_info = QuantityInfo(quantity=100, unit_price=1000)

    entry_data = {
        "no": "001",
        "description": "テスト商品",
        "tax_rate": "10%",
        "amount": "¥1,000",
        "page_no": 1,
        "stock_info": stock_info,
        "quantity_info": quantity_info,
        "date_range": "2024/01/01-2024/01/31",
    }
    entry = EntryDetail(**entry_data)
    assert entry.stock_info == stock_info
    assert entry.quantity_info == quantity_info
    assert entry.date_range == "2024/01/01-2024/01/31"


def test_customer_entry_creation():
    """CustomerEntryモデルの作成テスト"""
    customer_data = {
        "customer_code": "C001",
        "customer_name": "テスト顧客",
        "department": "営業部",
        "box_number": "BOX001",
    }
    customer = CustomerEntry(**customer_data)
    assert customer.customer_code == "C001"
    assert customer.customer_name == "テスト顧客"
    assert customer.department == "営業部"
    assert customer.box_number == "BOX001"
    assert customer.entries == []


def test_customer_entry_with_entries():
    """CustomerEntryモデルの明細付きテスト"""
    entry = EntryDetail(
        no="001",
        description="テスト商品",
        tax_rate="10%",
        amount="¥1,000",
        page_no=1,
    )
    customer_data = {
        "customer_code": "C001",
        "customer_name": "テスト顧客",
        "department": "営業部",
        "box_number": "BOX001",
        "entries": [entry],
    }
    customer = CustomerEntry(**customer_data)
    assert len(customer.entries) == 1
    assert customer.entries[0] == entry


def test_document_structure_creation():
    """DocumentStructureモデルの作成テスト"""
    document_data = {
        "pdf_filename": "test.pdf",
        "total_amount": "¥10,000",
    }
    document = DocumentStructure(**document_data)
    assert document.pdf_filename == "test.pdf"
    assert document.total_amount == "¥10,000"
    assert document.customers == []


def test_document_structure_with_customers():
    """DocumentStructureモデルの顧客情報付きテスト"""
    entry = EntryDetail(
        no="001",
        description="テスト商品",
        tax_rate="10%",
        amount="¥1,000",
        page_no=1,
    )
    customer = CustomerEntry(
        customer_code="C001",
        customer_name="テスト顧客",
        department="営業部",
        box_number="BOX001",
        entries=[entry],
    )
    document_data = {
        "pdf_filename": "test.pdf",
        "total_amount": "¥10,000",
        "customers": [customer],
    }
    document = DocumentStructure(**document_data)
    assert len(document.customers) == 1
    assert document.customers[0] == customer
    assert len(document.customers[0].entries) == 1
    assert document.customers[0].entries[0] == entry


def test_document_structure_validation():
    """DocumentStructureモデルのバリデーションテスト"""
    # 必須フィールドの欠落
    with pytest.raises(ValidationError):
        DocumentStructure(total_amount="¥10,000")  # pdf_filenameが欠落

    with pytest.raises(ValidationError):
        DocumentStructure(pdf_filename="test.pdf")  # total_amountが欠落
