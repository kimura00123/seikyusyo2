"""
エクセル出力エンジンのテスト
"""

import os
import pytest
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Border, Side, Alignment

from src.core.excel_exporter import ExcelExporter
from src.core.structuring import (
    DocumentStructure,
    CustomerEntry,
    EntryDetail,
    StockInfo,
    QuantityInfo,
)


@pytest.fixture
def sample_data() -> DocumentStructure:
    """テスト用のサンプルデータを提供"""
    return DocumentStructure(
        pdf_filename="test.pdf",
        total_amount="¥10,000",
        customers=[
            CustomerEntry(
                customer_code="C001",
                customer_name="テスト顧客",
                department="営業部",
                box_number="BOX001",
                entries=[
                    EntryDetail(
                        no="001",
                        description="テスト商品1",
                        tax_rate="10%",
                        amount="¥1,000",
                        page_no=1,
                        date_range="2024/01/01-2024/01/31",
                        stock_info=StockInfo(
                            carryover=100,
                            incoming=50,
                            w_value=30,
                            outgoing=20,
                            remaining=130,
                            total=180,
                            unit_price=1000,
                        ),
                        quantity_info=QuantityInfo(quantity=100, unit_price=1000),
                    ),
                    EntryDetail(
                        no="002",
                        description="テスト商品2",
                        tax_rate="8%",
                        amount="¥2,000",
                        page_no=1,
                        date_range=None,
                        stock_info=None,
                        quantity_info=None,
                    ),
                ],
            )
        ],
    )


class TestExcelExporter:
    """ExcelExporterクラスのテスト"""

    @pytest.fixture
    def exporter(self):
        """ExcelExporterインスタンスを提供"""
        return ExcelExporter()

    def test_style_initialization(self, exporter):
        """スタイル設定の初期化テスト"""
        # ヘッダーの背景色
        assert exporter.header_fill.start_color.rgb in ["1976D2", "001976D2"]
        assert exporter.header_fill.end_color.rgb in ["1976D2", "001976D2"]
        assert exporter.header_fill.fill_type == "solid"

        # フォント
        assert exporter.header_font.color.rgb == "FFFFFF"
        assert exporter.header_font.bold is True

        # 罫線
        assert all(
            side.style == "thin"
            for side in [
                exporter.border.left,
                exporter.border.right,
                exporter.border.top,
                exporter.border.bottom,
            ]
        )

        # 配置
        assert exporter.center_alignment.horizontal == "center"
        assert exporter.center_alignment.vertical == "center"
        assert exporter.wrap_alignment.vertical == "center"
        assert exporter.wrap_alignment.wrap_text is True

    def test_export_to_excel_with_filename(self, exporter, sample_data, tmp_path):
        """ファイル名指定でのエクセル出力テスト"""
        output_dir = tmp_path / "excel"
        filename = "test_output.xlsx"

        # エクセルファイルの出力
        output_path = exporter.export_to_excel(sample_data, str(output_dir), filename)

        # ファイルの存在確認
        assert os.path.exists(output_path)
        assert os.path.basename(output_path) == filename

        # ワークブックの検証
        wb = load_workbook(output_path)
        ws = wb.active

        # シート名の確認
        assert ws.title == "請求書データ"

        # ヘッダー行の検証
        headers = [cell.value for cell in ws[1]]
        assert "PDF名" in headers
        assert "顧客コード" in headers
        assert "明細番号" in headers
        assert "繰越在庫" in headers
        assert "数量" in headers

        # データ行の検証（1行目）
        assert ws.cell(row=2, column=1).value == "test.pdf"  # PDF名
        assert ws.cell(row=2, column=3).value == "C001"  # 顧客コード
        assert ws.cell(row=2, column=7).value == "001"  # 明細番号
        assert ws.cell(row=2, column=13).value == 100  # 繰越在庫
        assert ws.cell(row=2, column=20).value == 100  # 数量

        # データ行の検証（2行目）
        assert ws.cell(row=3, column=1).value == "test.pdf"  # PDF名
        assert ws.cell(row=3, column=3).value == "C001"  # 顧客コード
        assert ws.cell(row=3, column=7).value == "002"  # 明細番号
        assert ws.cell(row=3, column=13).value is None  # 繰越在庫（なし）
        assert ws.cell(row=3, column=20).value is None  # 数量（なし）

        # スタイルの検証
        # ヘッダー行
        for cell in ws[1]:
            assert cell.fill.start_color.rgb in ["1976D2", "001976D2"]
            assert cell.font.color.rgb == "FFFFFF"
            assert cell.border.left.style == "thin"
            assert cell.alignment.horizontal == "center"

        # データ行
        for row in ws.iter_rows(min_row=2, max_row=3):
            for cell in row:
                assert cell.border.left.style == "thin"
                # 摘要列は折り返し設定
                if cell.column == 8:
                    assert cell.alignment.wrap_text is True
                else:
                    assert cell.alignment.horizontal == "center"

    def test_export_to_excel_without_filename(self, exporter, sample_data, tmp_path):
        """ファイル名未指定でのエクセル出力テスト"""
        output_dir = tmp_path / "excel"

        # エクセルファイルの出力
        output_path = exporter.export_to_excel(sample_data, str(output_dir))

        # ファイルの存在確認
        assert os.path.exists(output_path)
        assert output_path.endswith(".xlsx")

        # ファイル名のフォーマット確認
        filename = os.path.basename(output_path)
        assert filename.startswith("invoice_data_")
        assert filename.endswith(".xlsx")

        # タイムスタンプ部分の検証
        timestamp = filename.replace("invoice_data_", "").replace(".xlsx", "")
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS
        datetime.strptime(timestamp, "%Y%m%d_%H%M%S")  # エラーが発生しないことを確認

    def test_export_to_excel_with_invalid_path(self, exporter, sample_data):
        """無効なパスでのエクセル出力テスト"""
        with pytest.raises(OSError):
            # Windowsで無効なパス文字を含むパスを指定
            exporter.export_to_excel(sample_data, "invalid/path/*:<>")

    def test_export_to_excel_with_empty_data(self, exporter, tmp_path):
        """空のデータでのエクセル出力テスト"""
        output_dir = tmp_path / "excel"
        empty_data = DocumentStructure(
            pdf_filename="test.pdf",
            total_amount="¥0",
            customers=[],
        )

        # エクセルファイルの出力
        output_path = exporter.export_to_excel(empty_data, str(output_dir))

        # ファイルの存在確認
        assert os.path.exists(output_path)

        # ワークブックの検証
        wb = load_workbook(output_path)
        ws = wb.active

        # ヘッダー行のみ存在することを確認
        assert ws.max_row == 1
