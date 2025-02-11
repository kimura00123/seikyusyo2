import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTPage,
    LTTextContainer,
    LTChar,
    LTTextLineHorizontal,
    LTTextBoxHorizontal,
)
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextElement:
    """テキスト要素の情報"""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int
    font_name: Optional[str] = None
    font_size: Optional[float] = None


class PDFParser:
    """PDFからテキストと位置情報を抽出するクラス"""

    def __init__(self):
        # A4サイズの寸法（ポイント単位）
        self.page_width = 595
        self.page_height = 842

    def extract_text_with_positions(
        self, pdf_path: str
    ) -> Dict[int, List[TextElement]]:
        """
        PDFからテキストと位置情報を抽出する

        Args:
            pdf_path (str): PDFファイルのパス

        Returns:
            Dict[int, List[TextElement]]: ページ毎のテキスト要素リスト
        """
        try:
            result = {}
            current_page = 0

            for page_layout in extract_pages(pdf_path):
                if not isinstance(page_layout, LTPage):
                    continue

                current_page += 1
                result[current_page] = self._process_page(page_layout, current_page)

            logger.info(f"PDFからテキストを抽出: {len(result)}ページ")
            return result

        except Exception as e:
            logger.error(f"PDFの解析でエラー: {e}", exc_info=True)
            raise

    def _process_page(self, page_layout: LTPage, page_num: int) -> List[TextElement]:
        """
        ページからテキスト要素を抽出する

        Args:
            page_layout (LTPage): ページのレイアウト情報
            page_num (int): ページ番号

        Returns:
            List[TextElement]: テキスト要素のリスト
        """
        elements = []

        # テキスト要素を上から下に並べ替え
        text_elements = sorted(
            [elem for elem in page_layout if isinstance(elem, LTTextContainer)],
            key=lambda x: -x.y1,
        )

        for element in text_elements:
            # 文字要素の取得
            chars = []
            if isinstance(element, (LTTextLineHorizontal, LTTextBoxHorizontal)):
                for obj in element:
                    if isinstance(obj, LTChar):
                        chars.append(obj)

            # フォント情報の取得
            font_info = self._extract_font_info(chars) if chars else (None, None)

            # テキスト要素の作成
            text_element = TextElement(
                text=element.get_text().strip(),
                x0=element.x0,
                y0=element.y0,
                x1=element.x1,
                y1=element.y1,
                page=page_num,
                font_name=font_info[0],
                font_size=font_info[1],
            )
            elements.append(text_element)

        return elements

    def _extract_font_info(
        self, chars: List[LTChar]
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        文字要素からフォント情報を抽出する

        Args:
            chars (List[LTChar]): 文字要素のリスト

        Returns:
            Tuple[Optional[str], Optional[float]]: フォント名とサイズのタプル
        """
        if not chars:
            return None, None

        # 最も頻出するフォント情報を使用
        font_counts = {}
        size_sum = 0

        for char in chars:
            font_name = getattr(char, "fontname", None)
            if font_name:
                font_counts[font_name] = font_counts.get(font_name, 0) + 1
            size_sum += getattr(char, "size", 0)

        # フォント名の決定
        font_name = (
            max(font_counts.items(), key=lambda x: x[1])[0] if font_counts else None
        )

        # フォントサイズの決定（平均値）
        font_size = size_sum / len(chars) if chars else None

        return font_name, font_size

    def get_page_dimensions(self, pdf_path: str) -> List[Tuple[float, float]]:
        """
        PDFの各ページの寸法を取得する

        Args:
            pdf_path (str): PDFファイルのパス

        Returns:
            List[Tuple[float, float]]: ページ毎の(幅, 高さ)のリスト
        """
        try:
            dimensions = []
            for page_layout in extract_pages(pdf_path):
                if isinstance(page_layout, LTPage):
                    dimensions.append((page_layout.width, page_layout.height))
            return dimensions

        except Exception as e:
            logger.error(f"ページ寸法の取得でエラー: {e}", exc_info=True)
            raise

    def validate_pdf_version(self, pdf_path: str) -> bool:
        """
        PDFバージョンを検証する

        Args:
            pdf_path (str): PDFファイルのパス

        Returns:
            bool: PDFバージョンが1.4以上の場合はTrue
        """
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(8).decode("ascii")
                version = float(header[5:8])
                return version >= 1.4

        except Exception as e:
            logger.error(f"PDFバージョンの検証でエラー: {e}", exc_info=True)
            return False


# 使用例:
"""
parser = PDFParser()

# テキストと位置情報の抽出
text_elements = parser.extract_text_with_positions("invoice.pdf")

# ページ寸法の取得
dimensions = parser.get_page_dimensions("invoice.pdf")

# PDFバージョンの検証
is_valid = parser.validate_pdf_version("invoice.pdf")
"""
