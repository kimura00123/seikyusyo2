import os
from datetime import datetime
from pathlib import Path
from typing import List
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from utils.logger import get_logger
from core.structuring import DocumentStructure, CustomerEntry, EntryDetail

logger = get_logger(__name__)


class ExcelExporter:
    """エクセル出力エンジン"""

    def __init__(self):
        # スタイル設定
        self.header_fill = PatternFill(
            start_color="1976D2", end_color="1976D2", fill_type="solid"
        )
        self.header_font = Font(color="FFFFFF", bold=True)
        self.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        self.center_alignment = Alignment(horizontal="center", vertical="center")
        self.wrap_alignment = Alignment(vertical="center", wrap_text=True)

    def export_to_excel(
        self, data: DocumentStructure, output_dir: str, filename: str = None
    ) -> str:
        """
        構造化データをエクセルファイルに出力する

        Args:
            data (DocumentStructure): 出力対象のデータ
            output_dir (str): 出力ディレクトリのパス
            filename (str, optional): 出力ファイル名。指定がない場合は自動生成

        Returns:
            str: 生成されたファイルのパス
        """
        try:
            # 出力ディレクトリの作成
            os.makedirs(output_dir, exist_ok=True)

            # ファイル名の生成
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"invoice_data_{timestamp}.xlsx"

            output_path = os.path.join(output_dir, filename)

            # ワークブックの作成
            wb = Workbook()
            ws = wb.active
            ws.title = "請求書データ"

            # ヘッダーの設定
            headers = [
                # ドキュメント情報
                "PDF名",
                "合計金額",
                # 顧客情報
                "顧客コード",
                "顧客名",
                "部署",
                "文書箱番号",
                # 明細情報
                "明細番号",
                "摘要",
                "税率",
                "金額",
                "日付範囲",
                "ページ",
                # 在庫情報
                "繰越在庫",
                "入庫数",
                "W値",
                "出庫数",
                "在庫残高",
                "合計",
                "単価",
                # 数量情報
                "数量",
                "数量単価",
            ]

            # ヘッダー行の書き込み
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.fill = self.header_fill
                cell.font = self.header_font
                cell.border = self.border
                cell.alignment = self.center_alignment

            # データの書き込み
            row = 2
            for customer in data.customers:
                for entry in customer.entries:
                    # 基本情報
                    ws.cell(row=row, column=1, value=data.pdf_filename)
                    ws.cell(row=row, column=2, value=data.total_amount)

                    # 顧客情報
                    ws.cell(row=row, column=3, value=customer.customer_code)
                    ws.cell(row=row, column=4, value=customer.customer_name)
                    ws.cell(row=row, column=5, value=customer.department)
                    ws.cell(row=row, column=6, value=customer.box_number)

                    # 明細情報
                    ws.cell(row=row, column=7, value=entry.no)
                    ws.cell(row=row, column=8, value=entry.description)
                    ws.cell(row=row, column=9, value=entry.tax_rate)
                    ws.cell(row=row, column=10, value=entry.amount)
                    ws.cell(row=row, column=11, value=entry.date_range)
                    ws.cell(row=row, column=12, value=entry.page_no)

                    # 在庫情報
                    if entry.stock_info:
                        ws.cell(row=row, column=13, value=entry.stock_info.carryover)
                        ws.cell(row=row, column=14, value=entry.stock_info.incoming)
                        ws.cell(row=row, column=15, value=entry.stock_info.w_value)
                        ws.cell(row=row, column=16, value=entry.stock_info.outgoing)
                        ws.cell(row=row, column=17, value=entry.stock_info.remaining)
                        ws.cell(row=row, column=18, value=entry.stock_info.total)
                        ws.cell(row=row, column=19, value=entry.stock_info.unit_price)

                    # 数量情報
                    if entry.quantity_info:
                        ws.cell(row=row, column=20, value=entry.quantity_info.quantity)
                        ws.cell(
                            row=row, column=21, value=entry.quantity_info.unit_price
                        )

                    # スタイルの適用
                    for col in range(1, len(headers) + 1):
                        cell = ws.cell(row=row, column=col)
                        cell.border = self.border
                        cell.alignment = (
                            self.wrap_alignment
                            if col in [8]  # 摘要列は折り返し
                            else self.center_alignment
                        )

                    row += 1

            # 列幅の自動調整
            for col in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].auto_size = True

            # ファイルの保存
            wb.save(output_path)
            logger.info(f"エクセルファイルを出力: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"エクセル出力でエラー: {e}", exc_info=True)
            raise


# 使用例:
"""
exporter = ExcelExporter()

# エクセルファイルの出力
output_path = exporter.export_to_excel(
    structured_data,
    "output/excel",
    "invoice_data.xlsx"
)
"""
