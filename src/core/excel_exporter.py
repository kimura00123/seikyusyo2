import os
from typing import Dict, Any, Union, List, Optional
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from .structuring import DocumentStructure, CustomerEntry, EntryDetail
from src.utils.config import get_settings

settings = get_settings()

class ExcelExporter:
    def __init__(self):
        self.workbook = Workbook()
        self.sheet = self.workbook.active
        self.sheet.title = "請求書データ"
        self._setup_styles()
        self.headers = [
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
            "在庫",
            "入庫",
            "W値",
            "出庫",
            "残高",
            "合計",
            "単価",
            "荷役数、廃棄数、段ボール数",
            "単価",
            # フィルタ補助用の列を追加
            "業務区分",
            "業務内容",
            "業務日付"
        ]
        
        # フィルタ用のマッピングを定義
        self.product_type_mapping = {
            "保管料 文書箱": {"type": "保管", "detail": "保管"},
            "荷役料 - 新規入庫 文書箱": {"type": "荷役", "detail": "新規入庫"},
            "荷役料 - 出庫 文書箱": {"type": "荷役", "detail": "出庫"},
            "荷役料 - 永久出庫 文書箱": {"type": "荷役", "detail": "永久出庫"},
            "運搬料 - 寺田便 文書箱": {"type": "運搬", "detail": "入出庫"},
            "A4文書用ダンボール": {"type": "運搬", "detail": "段ボール"},
            "廃棄手数料 文書箱": {"type": "運搬", "detail": "廃棄"}
        }

    def _setup_styles(self):
        """スタイルの設定"""
        self.header_font = Font(bold=True)
        self.header_fill = PatternFill(
            start_color="CCCCCC", end_color="CCCCCC", fill_type="solid"
        )
        self.center_align = Alignment(horizontal="center")
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    def _extract_date_from_period(self, period: str) -> str:
        """期間から日付を抽出する"""
        if not period:
            return ""
            
        # 括弧内の日付を抽出 例: 2024/08月分(2024/08/09) -> 2024/08/09
        try:
            if "(" in period and ")" in period:
                date_part = period.split("(")[1].split(")")[0]
                # 範囲がある場合は最初の日付を使用
                if " - " in date_part:
                    date_part = date_part.split(" - ")[0]
                return date_part
            return ""
        except:
            return ""

    def _get_product_type_info(self, product_name: str) -> dict:
        """商品名から業務タイプと詳細を取得する"""
        for key, value in self.product_type_mapping.items():
            if product_name and key in product_name:
                return value
        return {"type": "", "detail": ""}

    def export(
        self, document: Union[DocumentStructure, Dict[str, Any]], output_path: str
    ) -> None:
        """エクセルファイルを出力する"""
        # ヘッダー行の書き込み
        for col, header in enumerate(self.headers, 1):
            cell = self.sheet.cell(row=1, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_align
            cell.border = self.border

        # データの書き込み
        row = 2
        # documentがdict型の場合は直接アクセス、そうでない場合は属性アクセス
        doc_data = document if isinstance(document, dict) else document.model_dump()

        for customer in doc_data["customers"]:
            for entry in customer["entries"]:
                # 基本情報の書き込み
                self.sheet.cell(row=row, column=1).value = doc_data["pdf_filename"]
                self.sheet.cell(row=row, column=2).value = doc_data["total_amount"]
                self.sheet.cell(row=row, column=3).value = customer["customer_code"]
                self.sheet.cell(row=row, column=4).value = customer["customer_name"]
                self.sheet.cell(row=row, column=5).value = customer["department"]
                self.sheet.cell(row=row, column=6).value = customer["box_number"]
                self.sheet.cell(row=row, column=7).value = entry["no"]
                self.sheet.cell(row=row, column=8).value = entry["description"]
                self.sheet.cell(row=row, column=9).value = entry["tax_rate"]
                self.sheet.cell(row=row, column=10).value = entry["amount"]
                self.sheet.cell(row=row, column=11).value = entry.get("date_range")
                self.sheet.cell(row=row, column=12).value = entry["page_no"]

                # 在庫情報の書き込み
                if "stock_info" in entry and entry["stock_info"]:
                    stock_info = entry["stock_info"]
                    self.sheet.cell(row=row, column=13).value = stock_info.get("carryover")
                    self.sheet.cell(row=row, column=14).value = stock_info.get("incoming")
                    self.sheet.cell(row=row, column=15).value = stock_info.get("w_value")
                    self.sheet.cell(row=row, column=16).value = stock_info.get("outgoing")
                    self.sheet.cell(row=row, column=17).value = stock_info.get("remaining")
                    self.sheet.cell(row=row, column=18).value = stock_info.get("total")
                    self.sheet.cell(row=row, column=19).value = stock_info.get("unit_price")

                # 数量情報の書き込み
                if "quantity_info" in entry and entry["quantity_info"]:
                    quantity_info = entry["quantity_info"]
                    self.sheet.cell(row=row, column=20).value = quantity_info.get("quantity")
                    self.sheet.cell(row=row, column=21).value = quantity_info.get("unit_price")

                # フィルタ補助用の情報を書き込み
                product_type_info = self._get_product_type_info(entry["description"])
                self.sheet.cell(row=row, column=22).value = product_type_info["type"]
                self.sheet.cell(row=row, column=23).value = product_type_info["detail"]
                self.sheet.cell(row=row, column=24).value = self._extract_date_from_period(entry.get("date_range", ""))
                
                # セルにボーダーを適用
                for col in range(1, len(self.headers) + 1):
                    self.sheet.cell(row=row, column=col).border = self.border

                row += 1

        # テーブルの定義
        table_range = f"A1:{get_column_letter(len(self.headers))}{row-1}"
        table = Table(displayName="InvoiceTable", ref=table_range)
        
        # テーブルスタイルの設定
        style = TableStyleInfo(
            name="TableStyleMedium2", showFirstColumn=False,
            showLastColumn=False, showRowStripes=True, showColumnStripes=False
        )
        table.tableStyleInfo = style
        
        # テーブルをシートに追加
        self.sheet.add_table(table)

        # サンプルのフィルタ表示用名前付き範囲を定義
        self._create_named_ranges()
        
        # フィルタ用補助シートを追加
        self._add_helper_sheet()

        # 列幅の自動調整
        for col in range(1, len(self.headers) + 1):
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

    def _create_named_ranges(self):
        """XLOOKUPで使いやすいように名前付き範囲を定義"""
        # 全体のデータ範囲
        self.workbook.create_named_range(
            "AllData", 
            self.sheet, 
            f"$A$1:${get_column_letter(len(self.headers))}${self.sheet.max_row}"
        )
        
        # 保管データ用の名前付き範囲
        self.workbook.create_named_range(
            "StorageData", 
            self.sheet, 
            f'=FILTER(InvoiceTable, InvoiceTable[業務区分]="保管")'
        )
        
        # 荷役データ用の名前付き範囲
        self.workbook.create_named_range(
            "HandlingData", 
            self.sheet, 
            f'=FILTER(InvoiceTable, InvoiceTable[業務区分]="荷役")'
        )
        
        # 運搬データ用の名前付き範囲
        self.workbook.create_named_range(
            "TransportData", 
            self.sheet, 
            f'=FILTER(InvoiceTable, InvoiceTable[業務区分]="運搬")'
        )

    def _add_helper_sheet(self):
        """フィルタ補助シートを追加"""
        helper_sheet = self.workbook.create_sheet(title="フィルタヘルパー")
        
        # フィルタ説明の追加
        helper_sheet["A1"] = "フィルタと名前付き範囲の使用方法"
        helper_sheet["A1"].font = Font(bold=True, size=14)
        
        helper_sheet["A3"] = "主な名前付き範囲："
        helper_sheet["A3"].font = Font(bold=True)
        
        helper_sheet["A4"] = "InvoiceTable - 全データを含むテーブル"
        helper_sheet["A5"] = "StorageData - 保管業務のみのデータ"
        helper_sheet["A6"] = "HandlingData - 荷役業務のみのデータ"
        helper_sheet["A7"] = "TransportData - 運搬業務のみのデータ"
        
        helper_sheet["A9"] = "XLOOKUP使用例："
        helper_sheet["A9"].font = Font(bold=True)
        
        helper_sheet["A10"] = "=XLOOKUP(検索値, StorageData[BOX番号], StorageData[在庫情報_合計])"
        helper_sheet["A11"] = "=XLOOKUP(検索値, HandlingData[BOX番号], HandlingData[数量情報_数量])"
        
        helper_sheet["A13"] = "フィルタの使用方法："
        helper_sheet["A13"].font = Font(bold=True)
        
        helper_sheet["A14"] = "1. データシートの「業務区分」や「業務内容」列でフィルタリングできます。"
        helper_sheet["A15"] = "2. スライサーを追加すると視覚的にフィルタリングが可能になります。"
        helper_sheet["A16"] = "3. フィルタ済みのテーブルを元にXLOOKUPを使用すれば、自動的にフィルタ条件に合致する値のみが対象になります。"
        
        helper_sheet["A18"] = "補助列について："
        helper_sheet["A18"].font = Font(bold=True)
        
        helper_sheet["A19"] = "業務区分: 保管、荷役、運搬などの大分類"
        helper_sheet["A20"] = "業務内容: 入庫、出庫、廃棄などの詳細分類"
        helper_sheet["A21"] = "業務日付: 期間から抽出した実際の日付（運搬業務の日付フィルタ用）"
        
        # 列幅の調整
        helper_sheet.column_dimensions["A"].width = 100
