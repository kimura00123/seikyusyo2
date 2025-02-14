"""
PDFパーサーのテスト
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.core.pdf_parser import PDFParser, TextElement
from pdfminer.layout import (
    LTPage,
    LTTextContainer,
    LTChar,
    LTTextLineHorizontal,
    LTTextBoxHorizontal,
)


def test_text_element_model():
    """TextElementモデルのテスト"""
    # 必須フィールドのみ
    element = TextElement(
        text="テスト",
        x0=100.0,
        y0=200.0,
        x1=150.0,
        y1=220.0,
        page=1,
    )
    assert element.text == "テスト"
    assert element.x0 == 100.0
    assert element.y0 == 200.0
    assert element.x1 == 150.0
    assert element.y1 == 220.0
    assert element.page == 1
    assert element.font_name is None
    assert element.font_size is None

    # 全フィールド指定
    element = TextElement(
        text="テスト",
        x0=100.0,
        y0=200.0,
        x1=150.0,
        y1=220.0,
        page=1,
        font_name="Arial",
        font_size=12.0,
    )
    assert element.font_name == "Arial"
    assert element.font_size == 12.0


class TestPDFParser:
    """PDFParserクラスのテスト"""

    @pytest.fixture
    def parser(self):
        """PDFParserインスタンスを提供"""
        return PDFParser()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """テスト用のPDFファイルパスを提供"""
        pdf_path = tmp_path / "test.pdf"
        # PDFヘッダーを作成（バージョン1.4）
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n")
        return str(pdf_path)

    def test_extract_text_with_positions(self, parser, sample_pdf_path, mocker):
        """テキスト抽出のテスト"""
        # モックの作成
        mock_page = MagicMock(spec=LTPage)
        mock_text = MagicMock(spec=LTTextContainer)
        mock_text.get_text.return_value = "テストテキスト"
        mock_text.x0, mock_text.y0 = 100, 200
        mock_text.x1, mock_text.y1 = 150, 220

        mock_page.__iter__.return_value = [mock_text]
        mocker.patch(
            "src.core.pdf_parser.extract_pages",
            return_value=[mock_page],
        )

        # テスト実行
        result = parser.extract_text_with_positions(sample_pdf_path)

        # 結果の検証
        assert len(result) == 1  # 1ページ
        assert len(result[1]) == 1  # 1つのテキスト要素
        element = result[1][0]
        assert element.text == "テストテキスト"
        assert element.x0 == 100
        assert element.y0 == 200
        assert element.x1 == 150
        assert element.y1 == 220
        assert element.page == 1

    def test_process_page(self, parser):
        """ページ処理のテスト"""
        # モックの作成
        page = MagicMock(spec=LTPage)
        text_line = MagicMock(spec=LTTextLineHorizontal)
        char = MagicMock(spec=LTChar)
        char.fontname = "Arial"
        char.size = 12.0

        text_line.get_text.return_value = "テストテキスト"
        text_line.x0, text_line.y0 = 100, 200
        text_line.x1, text_line.y1 = 150, 220
        text_line.__iter__.return_value = [char]

        page.__iter__.return_value = [text_line]

        # テスト実行
        result = parser._process_page(page, 1)

        # 結果の検証
        assert len(result) == 1
        element = result[0]
        assert element.text == "テストテキスト"
        assert element.font_name == "Arial"
        assert element.font_size == 12.0

    def test_extract_font_info(self, parser):
        """フォント情報抽出のテスト"""
        # モックの作成
        char1 = MagicMock(spec=LTChar)
        char1.fontname = "Arial"
        char1.size = 12.0

        char2 = MagicMock(spec=LTChar)
        char2.fontname = "Arial"
        char2.size = 12.0

        char3 = MagicMock(spec=LTChar)
        char3.fontname = "Times"
        char3.size = 10.0

        # テスト実行
        font_name, font_size = parser._extract_font_info([char1, char2, char3])

        # 結果の検証
        assert font_name == "Arial"  # 最も頻出するフォント名
        assert font_size == 11.333333333333334  # 平均サイズ

        # 空のリストの場合
        font_name, font_size = parser._extract_font_info([])
        assert font_name is None
        assert font_size is None

    def test_get_page_dimensions(self, parser, sample_pdf_path, mocker):
        """ページ寸法取得のテスト"""
        # モックの作成
        mock_page = MagicMock(spec=LTPage)
        mock_page.width = 595
        mock_page.height = 842

        mocker.patch(
            "src.core.pdf_parser.extract_pages",
            return_value=[mock_page],
        )

        # テスト実行
        dimensions = parser.get_page_dimensions(sample_pdf_path)

        # 結果の検証
        assert len(dimensions) == 1
        assert dimensions[0] == (595, 842)

    def test_validate_pdf_version(self, parser, tmp_path):
        """PDFバージョン検証のテスト"""
        # バージョン1.4のPDF
        pdf_path_1_4 = tmp_path / "test_1_4.pdf"
        with open(pdf_path_1_4, "wb") as f:
            f.write(b"%PDF-1.4\n")
        assert parser.validate_pdf_version(str(pdf_path_1_4)) is True

        # バージョン1.3のPDF
        pdf_path_1_3 = tmp_path / "test_1_3.pdf"
        with open(pdf_path_1_3, "wb") as f:
            f.write(b"%PDF-1.3\n")
        assert parser.validate_pdf_version(str(pdf_path_1_3)) is False

        # 不正なPDF
        invalid_pdf = tmp_path / "invalid.pdf"
        with open(invalid_pdf, "wb") as f:
            f.write(b"invalid")
        assert parser.validate_pdf_version(str(invalid_pdf)) is False

    def test_error_handling(self, parser):
        """エラーハンドリングのテスト"""
        # 存在しないファイル
        with pytest.raises(Exception):
            parser.extract_text_with_positions("/path/to/nonexistent.pdf")

        with pytest.raises(Exception):
            parser.get_page_dimensions("/path/to/nonexistent.pdf")

        # 不正なファイルパス
        assert parser.validate_pdf_version("") is False
