import os
from typing import Dict, Any
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from .structuring import DocumentStructure, CustomerEntry, EntryDetail


class ExcelExporter:
    def __init__(self):
        self.workbook = Workbook()
        self.sheet = self.workbook.active
        self.sheet.title = "請求書データ"
        self._setup_styles()

    def _setup_styles(self):
        """スタイルの設定"""
        self.header_font = Font(bold=True)
        self.header_fill = PatternFill(
            start_color="CCCCCC", end_color="CCCCCC", fill_type="solid"
        )
        self.center_align = Alignment(horizontal="center")

    def export(self, document: DocumentStructure, output_path: str) -> None:
        """エクセルファイルを出力する"""
        # ヘッダー行の設定
        headers = [
            "PDF名",
            "合計金額",
            "取引先コード",
            "取引先名",
            "部署",
            "BOX番号",
            "明細番号",
            "商品名",
            "税率",
            "金額",
            "期間",
            "ページ番号",
            "在庫情報_繰越",
            "在庫情報_入庫",
            "在庫情報_W値",
            "在庫情報_出庫",
            "在庫情報_残高",
            "在庫情報_合計",
            "在庫情報_単価",
            "数量情報_数量",
            "数量情報_単価",
        ]

        # ヘッダー行の書き込み
        for col, header in enumerate(headers, 1):
            cell = self.sheet.cell(row=1, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align

        # データの書き込み
        row = 2
        for customer in document.customers:
            for entry in customer.entries:
                self.sheet.cell(row=row, column=1).value = document.pdf_filename
                self.sheet.cell(row=row, column=2).value = document.total_amount
                self.sheet.cell(row=row, column=3).value = customer.customer_code
                self.sheet.cell(row=row, column=4).value = customer.customer_name
                self.sheet.cell(row=row, column=5).value = customer.department
                self.sheet.cell(row=row, column=6).value = customer.box_number
                self.sheet.cell(row=row, column=7).value = entry.no
                self.sheet.cell(row=row, column=8).value = entry.description
                self.sheet.cell(row=row, column=9).value = entry.tax_rate
                self.sheet.cell(row=row, column=10).value = entry.amount
                self.sheet.cell(row=row, column=11).value = entry.date_range
                self.sheet.cell(row=row, column=12).value = entry.page_no

                if entry.stock_info:
                    self.sheet.cell(row=row, column=13).value = (
                        entry.stock_info.carryover
                    )
                    self.sheet.cell(row=row, column=14).value = (
                        entry.stock_info.incoming
                    )
                    self.sheet.cell(row=row, column=15).value = entry.stock_info.w_value
                    self.sheet.cell(row=row, column=16).value = (
                        entry.stock_info.outgoing
                    )
                    self.sheet.cell(row=row, column=17).value = (
                        entry.stock_info.remaining
                    )
                    self.sheet.cell(row=row, column=18).value = entry.stock_info.total
                    self.sheet.cell(row=row, column=19).value = (
                        entry.stock_info.unit_price
                    )

                if entry.quantity_info:
                    self.sheet.cell(row=row, column=20).value = (
                        entry.quantity_info.quantity
                    )
                    self.sheet.cell(row=row, column=21).value = (
                        entry.quantity_info.unit_price
                    )

                row += 1

        # 列幅の自動調整
        for col in range(1, len(headers) + 1):
            max_length = 0
            column = get_column_letter(col)

            for cell in self.sheet[column]:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = max_length + 2
            self.sheet.column_dimensions[column].width = adjusted_width

        # ファイルの保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.workbook.save(output_path)
