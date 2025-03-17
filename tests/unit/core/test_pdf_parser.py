"""
PDFパーサーのテスト
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.core.pdf_parser import PDFParser
from pdfminer.layout import (
    LTPage,
    LTTextContainer,
    LTChar,
    LTTextLineHorizontal,
    LTTextBoxHorizontal,
)


class TestPDFParser:
    """PDFParserクラスのテスト"""

    @pytest.fixture
    def parser(self):
        """PDFParserインスタンスを提供"""
        return PDFParser("dummy.pdf")

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """テスト用のPDFファイルパスを提供"""
        pdf_path = tmp_path / "test.pdf"
        # PDFヘッダーを作成（バージョン1.4）
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n")
        return str(pdf_path)

    def test_extract_text_with_positions(self, parser, mocker):
        """テキスト抽出のテスト"""
        # pymupdf4llm.to_markdownのモック
        mock_to_markdown = mocker.patch("pymupdf4llm.to_markdown")
        mock_to_markdown.return_value = "# テスト文書\n\n## テスト見出し\n\nテストテキスト"

        # テスト実行
        result = parser.extract_text_with_positions()

        # 結果の検証
        assert isinstance(result, str)
        assert "# テスト文書" in result
        assert "## テスト見出し" in result
        assert "テストテキスト" in result
        mock_to_markdown.assert_called_once_with(parser.pdf_path)

    def test_get_page_dimensions(self, parser, mocker):
        """ページ寸法取得のテスト"""
        # PyMuPDFのモック
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.rect.width = 595
        mock_page.rect.height = 842
        mock_doc.__iter__.return_value = [mock_page]
        
        mock_fitz_open = mocker.patch("fitz.open", return_value=mock_doc)

        # テスト実行
        dimensions = parser.get_page_dimensions()

        # 結果の検証
        assert len(dimensions) == 1
        assert dimensions[0] == (595, 842)
        mock_fitz_open.assert_called_once_with(parser.pdf_path)
        mock_doc.close.assert_called_once()

    def test_validate_pdf_version(self, parser, tmp_path):
        """PDFバージョン検証のテスト"""
        # バージョン1.4のPDF
        pdf_path_1_4 = tmp_path / "test_1_4.pdf"
        with open(pdf_path_1_4, "wb") as f:
            f.write(b"%PDF-1.4\n")
            
        parser.pdf_path = str(pdf_path_1_4)
        assert parser.validate_pdf_version() is True

    def test_error_handling(self, mocker):
        """エラーハンドリングのテスト"""
        # pymupdf4llm.to_markdownが例外を発生させる場合
        mock_to_markdown = mocker.patch("pymupdf4llm.to_markdown")
        mock_to_markdown.side_effect = Exception("テストエラー")
        
        parser = PDFParser("/path/to/nonexistent.pdf")
        
        # extract_text_with_positionsが例外を再発生させることを確認
        with pytest.raises(Exception):
            parser.extract_text_with_positions()
