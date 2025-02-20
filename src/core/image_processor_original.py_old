from typing import List, Optional
import os
import re
from dataclasses import dataclass
import fitz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTPage


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

    def extract_detail_regions(self, pdf_path: str) -> List[DetailLine]:
        """PDFから明細行の位置情報を抽出する"""
        print(f"\n明細行の位置情報抽出開始: {pdf_path}")
        detail_lines = []
        current_page = 0

        for page_layout in extract_pages(pdf_path):
            if not isinstance(page_layout, LTPage):
                continue

            print(f"\nページ {current_page + 1} の処理開始")
            print(f"ページサイズ: 幅={page_layout.width}, 高さ={page_layout.height}")

            # 明細番号とその位置を収集
            number_positions = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    print(f"テキスト検出: {text}")
                    detail_no = self._is_detail_number(text)
                    if detail_no:
                        print(
                            f"明細番号を検出: No.{detail_no}, 位置: y1={element.y1}, y0={element.y0}"
                        )
                        number_positions.append((detail_no, element.y1, element.y0))

            # 明細番号の位置でソート（上から下）
            number_positions.sort(key=lambda x: -x[1])
            print(f"検出された明細番号: {len(number_positions)}個")

            # ページの余白（上下40ポイント）を考慮したページ範囲
            page_top = page_layout.height - 40
            page_bottom = 40

            # 各明細行の範囲を決定
            for i, (detail_no, y1, y0) in enumerate(number_positions):
                # 上端は現在の明細番号の位置
                y_top = y1 + 2  # 2ポイントの余白を追加

                # 下端の決定
                if i < len(number_positions) - 1:
                    # 次の明細番号がある場合は、その位置まで
                    y_bottom = number_positions[i + 1][1] - 2  # 2ポイントの余白を追加
                else:
                    # ページ最後の明細の場合は、ページ下部まで
                    y_bottom = page_bottom

                detail_lines.append(
                    DetailLine(
                        page_num=current_page,
                        no=detail_no,
                        y_top=y_top,
                        y_bottom=y_bottom,
                        x_left=40,
                        x_right=page_layout.width - 30,  # 右端の余白を30ポイントに修正
                    )
                )

            current_page += 1

        return detail_lines

    def extract_detail_image(
        self, pdf_path: str, detail_no: str, output_path: str
    ) -> None:
        """明細行の画像を抽出する"""
        try:
            # 明細行の位置情報を取得
            detail_lines = self.extract_detail_regions(pdf_path)
            target_detail = next((d for d in detail_lines if d.no == detail_no), None)
            if not target_detail:
                raise Exception(f"明細番号 {detail_no} が見つかりません")

            print(f"明細行の抽出開始: detail_no={detail_no}")
            print(f"PDF path: {pdf_path}")
            print(f"Output path: {output_path}")
            print(f"Target detail: {target_detail}")

            # PDFを開く
            print("Opening PDF...")
            doc = fitz.open(pdf_path)
            page = doc[target_detail.page_num]
            print(f"PDF page size: {page.rect}")

            # 切り取り範囲を設定（y_topとy_bottomを入れ替えて正しい順序にする）
            clip_rect = fitz.Rect(
                target_detail.x_left,
                target_detail.y_bottom,  # 下端を先に指定
                target_detail.x_right,
                target_detail.y_top,  # 上端を後に指定
            )
            print(f"Clip rectangle: {clip_rect}")

            # 画像として抽出
            matrix = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            print(f"Matrix scale: {self.dpi / 72}")
            pix = page.get_pixmap(matrix=matrix, clip=clip_rect)
            print(f"Extracted image size: {pix.width}x{pix.height}")

            # 画像を保存
            print(f"Saving image to: {output_path}")
            pix.save(output_path)
            print(f"Image saved successfully")

            doc.close()
            print("PDF closed")

        except Exception as e:
            raise Exception(f"画像抽出に失敗しました: {str(e)}")

    def _is_detail_number(self, text: str) -> Optional[str]:
        """明細番号かどうかを判定する"""
        patterns = [r"^No.\s*(\d+)\s*$", r"^\s*(\d+)\s*$"]  # No.10 or No10  # 10

        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
