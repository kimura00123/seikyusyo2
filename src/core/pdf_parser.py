from typing import Dict, List
from src.utils.logger import get_logger
import pymupdf4llm  # 追加

logger = get_logger(__name__)

class PDFParser:
    def __init__(self, pdf_path: str):
        """PDFパーサーの初期化"""
        self.pdf_path = pdf_path

    def extract_text_with_positions(self) -> str:
        """PDFからテキストをMarkdown形式で抽出する"""
        try:
            # PDFをMarkdown形式に変換
            md_text = pymupdf4llm.to_markdown(self.pdf_path)  # PDFをMarkdownに変換

            logger.info(f"PDFの解析が完了しました: {self.pdf_path}")
            return md_text  # Markdownテキストをそのまま返す

        except Exception as e:
            logger.error(f"PDFの解析に失敗しました: {str(e)}")
            raise

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
            import fitz  # PyMuPDF
            doc = fitz.open(self.pdf_path)
            for page in doc:
                dimensions.append((page.rect.width, page.rect.height))
            doc.close()
            return dimensions
        except Exception as e:
            logger.error(f"ページ寸法の取得に失敗しました: {str(e)}")
            raise
