from typing import Dict, List, Optional
from dataclasses import dataclass
from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTPage,
    LTTextContainer,
    LTChar,
    LTAnno,
    LTTextLineHorizontal,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextElement:
    """テキスト要素を表すデータクラス"""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page: int


class PDFParser:
    def __init__(self, pdf_path: str):
        """PDFパーサーの初期化"""
        self.pdf_path = pdf_path

    def extract_text_with_positions(self) -> Dict[int, List[TextElement]]:
        """PDFからテキストと位置情報を抽出する"""
        result: Dict[int, List[TextElement]] = {}
        current_page = 0

        try:
            # ページごとに処理
            for page_layout in extract_pages(self.pdf_path):
                if not isinstance(page_layout, LTPage):
                    continue

                current_page += 1
                result[current_page] = []

                # テキスト要素の抽出
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        text = self._extract_text_from_container(element)
                        if text:
                            result[current_page].append(
                                TextElement(
                                    text=text,
                                    x0=element.x0,
                                    y0=element.y0,
                                    x1=element.x1,
                                    y1=element.y1,
                                    page=current_page,
                                )
                            )

            logger.info(f"PDFの解析が完了しました: {self.pdf_path}")
            return result

        except Exception as e:
            logger.error(f"PDFの解析に失敗しました: {str(e)}")
            raise

    def _extract_text_from_container(self, container: LTTextContainer) -> Optional[str]:
        """テキストコンテナからテキストを抽出する"""
        text = ""
        for text_line in container:
            if isinstance(text_line, LTTextLineHorizontal):
                for character in text_line:
                    if isinstance(character, LTChar):
                        text += character.get_text()
                    elif isinstance(character, LTAnno):
                        text += " "
        return text.strip() or None

    def validate_pdf_version(self) -> bool:
        """PDFバージョンの検証（1.4以上を推奨）"""
        try:
            # TODO: PDFバージョンの検証を実装
            return True
        except Exception as e:
            logger.error(f"PDFバージョンの検証に失敗しました: {str(e)}")
            return False

    def get_page_dimensions(self) -> List[tuple[float, float]]:
        """各ページの寸法を取得する"""
        dimensions = []
        try:
            for page_layout in extract_pages(self.pdf_path):
                if isinstance(page_layout, LTPage):
                    dimensions.append((page_layout.width, page_layout.height))
            return dimensions
        except Exception as e:
            logger.error(f"ページ寸法の取得に失敗しました: {str(e)}")
            raise
