import os
from typing import List, Tuple
from dataclasses import dataclass
import fitz  # PyMuPDF


@dataclass
class DetailLine:
    """明細行の情報を保持するクラス"""

    page_num: int
    no: str
    y_top: float
    y_bottom: float
    description: str = ""
    x_left: float = 40
    x_right: float = 800


class ImageProcessor:
    def __init__(self, dpi: int = 200):
        """画像処理クラスの初期化"""
        self.dpi = dpi
        self.pdf_height = 842  # A4サイズの高さ（ポイント単位）

    def extract_detail_image(
        self, pdf_path: str, detail_no: str, output_path: str
    ) -> None:
        """明細行の画像を抽出する"""
        try:
            # PDFを開く
            doc = fitz.open(pdf_path)

            # 明細番号から該当ページを特定（デモ用に1ページ目固定）
            page = doc[0]

            # 画像として抽出（デモ用に固定範囲）
            pix = page.get_pixmap(matrix=fitz.Matrix(self.dpi / 72, self.dpi / 72))
            pix.save(output_path)

            doc.close()

        except Exception as e:
            raise Exception(f"画像抽出に失敗しました: {str(e)}")

    def _collect_detail_numbers(
        self, page: fitz.Page
    ) -> List[Tuple[str, float, float]]:
        """ページ内の明細番号とその位置を収集する"""
        numbers = []
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text.startswith("No.") or text.isdigit():
                            numbers.append(
                                (
                                    text.replace("No.", "").strip(),
                                    span["bbox"][1],  # y0
                                    span["bbox"][3],  # y1
                                )
                            )
        return sorted(numbers, key=lambda x: -x[1])  # y座標の降順でソート

    def _determine_detail_regions(
        self, numbers: List[Tuple[str, float, float]], page_height: float, page_num: int
    ) -> List[DetailLine]:
        """明細行の範囲を決定する"""
        detail_lines = []
        for i, (no, y_top, y_bottom) in enumerate(numbers):
            # 次の明細行までを範囲とする（最後の明細は下端まで）
            if i < len(numbers) - 1:
                next_y_top = numbers[i + 1][1]
            else:
                next_y_top = 0

            detail_lines.append(
                DetailLine(
                    page_num=page_num,
                    no=no,
                    y_top=y_top + 5,  # マージンを追加
                    y_bottom=next_y_top - 5 if next_y_top > 0 else y_bottom - 5,
                )
            )

        return detail_lines
