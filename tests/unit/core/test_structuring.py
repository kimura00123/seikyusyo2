"""
構造化エンジンのテスト
"""

import pytest
from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock

from src.core.structuring import (
    StockInfo,
    QuantityInfo,
    EntryDetail,
    CustomerEntry,
    DocumentStructure,
    StructuringEngine,
)
from src.core.pdf_parser import TextElement


def test_stock_info_model():
    """StockInfoモデルのテスト"""
    # 全フィールドがオプショナル
    stock = StockInfo()
    assert stock.carryover is None
    assert stock.incoming is None
    assert stock.w_value is None
    assert stock.outgoing is None
    assert stock.remaining is None
    assert stock.total is None
    assert stock.unit_price is None

    # 全フィールドあり
    stock = StockInfo(
        carryover=100,
        incoming=50,
        w_value=30,
        outgoing=20,
        remaining=130,
        total=180,
        unit_price=1000,
    )
    assert stock.carryover == 100
    assert stock.incoming == 50
    assert stock.w_value == 30
    assert stock.outgoing == 20
    assert stock.remaining == 130
    assert stock.total == 180
    assert stock.unit_price == 1000


def test_quantity_info_model():
    """QuantityInfoモデルのテスト"""
    # 全フィールドがオプショナル
    quantity = QuantityInfo()
    assert quantity.quantity is None
    assert quantity.unit_price is None

    # 全フィールドあり
    quantity = QuantityInfo(quantity=100, unit_price=1000)
    assert quantity.quantity == 100
    assert quantity.unit_price == 1000


def test_entry_detail_model():
    """EntryDetailモデルのテスト"""
    # 必須フィールドのみ
    entry = EntryDetail(
        no="001",
        description="テスト商品",
        tax_rate="10%",
        amount="¥1,000",
        page_no=1,
    )
    assert entry.no == "001"
    assert entry.description == "テスト商品"
    assert entry.tax_rate == "10%"
    assert entry.amount == "¥1,000"
    assert entry.page_no == 1
    assert entry.stock_info is None
    assert entry.quantity_info is None
    assert entry.date_range is None

    # オプショナルフィールドあり
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
    entry = EntryDetail(
        no="001",
        description="テスト商品",
        tax_rate="10%",
        amount="¥1,000",
        page_no=1,
        stock_info=stock_info,
        quantity_info=quantity_info,
        date_range="2024/01/01-2024/01/31",
    )
    assert entry.stock_info == stock_info
    assert entry.quantity_info == quantity_info
    assert entry.date_range == "2024/01/01-2024/01/31"


def test_customer_entry_model():
    """CustomerEntryモデルのテスト"""
    # 必須フィールドのみ
    customer = CustomerEntry(
        customer_code="C001",
        customer_name="テスト顧客",
    )
    assert customer.customer_code == "C001"
    assert customer.customer_name == "テスト顧客"
    assert customer.department is None
    assert customer.box_number is None
    assert customer.entries == []

    # 全フィールドあり
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
    assert customer.department == "営業部"
    assert customer.box_number == "BOX001"
    assert len(customer.entries) == 1
    assert customer.entries[0] == entry


def test_document_structure_model():
    """DocumentStructureモデルのテスト"""
    # 必須フィールドのみ
    document = DocumentStructure(
        pdf_filename="test.pdf",
        total_amount="¥10,000",
    )
    assert document.pdf_filename == "test.pdf"
    assert document.total_amount == "¥10,000"
    assert document.customers == []

    # 顧客情報あり
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
    document = DocumentStructure(
        pdf_filename="test.pdf",
        total_amount="¥10,000",
        customers=[customer],
    )
    assert len(document.customers) == 1
    assert document.customers[0] == customer


class TestStructuringEngine:
    """StructuringEngineクラスのテスト"""

    @pytest.fixture
    def sample_text_elements(self) -> Dict[int, List[TextElement]]:
        """テスト用のテキスト要素を提供"""
        return {
            1: [
                TextElement(
                    text="テスト顧客",
                    x0=100,
                    y0=500,
                    x1=200,
                    y1=520,
                    font_name="Arial",
                    font_size=12,
                    page=1,
                ),
                TextElement(
                    text="¥1,000",
                    x0=300,
                    y0=500,
                    x1=400,
                    y1=520,
                    font_name="Arial",
                    font_size=12,
                    page=1,
                ),
            ],
            2: [
                TextElement(
                    text="明細1",
                    x0=100,
                    y0=500,
                    x1=200,
                    y1=520,
                    font_name="Arial",
                    font_size=12,
                    page=2,
                ),
            ],
        }

    def test_preprocess_text(self, sample_text_elements):
        """テキスト前処理のテスト"""
        engine = StructuringEngine()
        result = engine._preprocess_text(sample_text_elements)

        # 期待される出力形式の確認
        assert "[x:100.0,y:500.0][font:Arial,size:12.0] テスト顧客" in result
        assert "[x:300.0,y:500.0][font:Arial,size:12.0] ¥1,000" in result
        assert "=== ページ区切り ===" in result
        assert "[x:100.0,y:500.0][font:Arial,size:12.0] 明細1" in result

    def test_build_prompt(self):
        """プロンプト構築のテスト"""
        engine = StructuringEngine()
        prompt = engine._build_prompt("テストテキスト")

        # プロンプトに必要な要素が含まれているか確認
        assert "テストテキスト" in prompt
        assert '"pdf_filename":' in prompt
        assert '"total_amount":' in prompt
        assert '"customers":' in prompt
        assert '"stock_info":' in prompt
        assert '"quantity_info":' in prompt

    @pytest.mark.asyncio
    async def test_call_openai_api(self, mocker):
        """OpenAI API呼び出しのテスト"""
        # モックの設定
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        parsed={
                            "pdf_filename": "test.pdf",
                            "total_amount": "¥10,000",
                            "customers": [],
                        }
                    )
                )
            ]
        )
        mocker.patch("openai.AsyncAzureOpenAI", return_value=mock_client)

        engine = StructuringEngine()
        result = await engine._call_openai_api("テストテキスト")

        # APIが正しく呼び出されたか確認
        assert mock_client.beta.chat.completions.parse.called
        assert result["pdf_filename"] == "test.pdf"
        assert result["total_amount"] == "¥10,000"
        assert result["customers"] == []

    @pytest.mark.asyncio
    async def test_structure_invoice(self, sample_text_elements, mocker):
        """請求書構造化の統合テスト"""
        # モックの設定
        mock_client = AsyncMock()
        mock_client.beta.chat.completions.parse.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        parsed={
                            "pdf_filename": "test.pdf",
                            "total_amount": "¥10,000",
                            "customers": [
                                {
                                    "customer_code": "C001",
                                    "customer_name": "テスト顧客",
                                    "department": "営業部",
                                    "box_number": "BOX001",
                                    "entries": [
                                        {
                                            "no": "001",
                                            "description": "テスト商品",
                                            "tax_rate": "10%",
                                            "amount": "¥1,000",
                                            "page_no": 1,
                                        }
                                    ],
                                }
                            ],
                        }
                    )
                )
            ]
        )
        mocker.patch("openai.AsyncAzureOpenAI", return_value=mock_client)

        engine = StructuringEngine()
        result = await engine.structure_invoice(sample_text_elements)

        # 結果の検証
        assert isinstance(result, DocumentStructure)
        assert result.pdf_filename == "test.pdf"
        assert result.total_amount == "¥10,000"
        assert len(result.customers) == 1
        assert result.customers[0].customer_code == "C001"
        assert len(result.customers[0].entries) == 1
        assert result.customers[0].entries[0].no == "001"
