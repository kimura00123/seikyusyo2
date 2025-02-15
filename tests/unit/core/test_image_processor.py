"""
画像処理エンジンのテスト
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image, ImageDraw

from src.core.image_processor import DetailRegion, ImageProcessor
from pdfminer.layout import LTPage, LTTextContainer


def test_detail_region_model():
    """DetailRegionモデルのテスト"""
    # 必須フィールドのみ
    region = DetailRegion(
        page_num=1,
        no="001",
        y_top=100.0,
        y_bottom=50.0,
    )
    assert region.page_num == 1
    assert region.no == "001"
    assert region.y_top == 100.0
    assert region.y_bottom == 50.0
    assert region.description == ""
    assert region.x_left == 40
    assert region.x_right == 800

    # 全フィールド指定
    region = DetailRegion(
        page_num=1,
        no="001",
        y_top=100.0,
        y_bottom=50.0,
        description="テスト明細",
        x_left=50.0,
        x_right=750.0,
    )
    assert region.description == "テスト明細"
    assert region.x_left == 50.0
    assert region.x_right == 750.0


class TestImageProcessor:
    """ImageProcessorクラスのテスト"""

    @pytest.fixture
    def processor(self):
        """ImageProcessorインスタンスを提供"""
        return ImageProcessor()

    @pytest.fixture
    def sample_pdf_path(self, tmp_path):
        """テスト用のPDFファイルパスを提供"""
        return str(tmp_path / "test.pdf")

    @pytest.fixture
    def sample_image(self):
        """テスト用の画像を提供"""
        image = Image.new("RGB", (800, 1000), "white")
        draw = ImageDraw.Draw(image)
        draw.text((100, 100), "No.1", fill="black")
        draw.text((100, 300), "No.2", fill="black")
        return image

    def test_is_detail_number(self, processor):
        """明細番号判定のテスト"""
        # 正常系
        assert processor._is_detail_number("No.1") == "1"
        assert processor._is_detail_number("No. 1") == "1"
        assert processor._is_detail_number("1") == "1"
        assert processor._is_detail_number(" 1 ") == "1"

        # 異常系
        assert processor._is_detail_number("ABC") is None
        assert processor._is_detail_number("No.A") is None
        assert processor._is_detail_number("") is None
        assert processor._is_detail_number("No.1.2") is None

    def test_collect_detail_numbers(self, processor):
        """明細番号収集のテスト"""
        # モックの作成
        page = MagicMock(spec=LTPage)
        text1 = MagicMock(spec=LTTextContainer)
        text1.get_text.return_value = "No.1"
        text1.y0, text1.y1 = 480, 500

        text2 = MagicMock(spec=LTTextContainer)
        text2.get_text.return_value = "No.2"
        text2.y0, text2.y1 = 280, 300

        page.__iter__.return_value = [text1, text2]

        # テスト実行
        result = processor._collect_detail_numbers(page)

        # 結果の検証
        assert len(result) == 2
        assert result[0] == ("1", 500, 480)  # 上から下に並べ替えられている
        assert result[1] == ("2", 300, 280)

    def test_determine_detail_regions(self, processor):
        """明細行の範囲決定のテスト"""
        number_positions = [
            ("1", 500, 480),  # No.1: y_top=500, y_bottom=480
            ("2", 300, 280),  # No.2: y_top=300, y_bottom=280
        ]
        page_height = 842  # A4サイズ
        page_num = 1

        regions = processor._determine_detail_regions(
            number_positions, page_height, page_num
        )

        assert len(regions) == 2

        # No.1の領域検証
        assert regions[0].page_num == 1
        assert regions[0].no == "1"
        assert regions[0].y_top == min(510, page_height)  # マージン10を加算
        assert regions[0].y_bottom == 290  # No.2のy_top - マージン

        # No.2の領域検証
        assert regions[1].page_num == 1
        assert regions[1].no == "2"
        assert regions[1].y_top == 310  # y_top + マージン
        assert regions[1].y_bottom == 0  # ページ最下部

    @pytest.mark.asyncio
    async def test_extract_detail_regions(self, processor, sample_pdf_path, mocker):
        """明細行の抽出テスト"""
        # extract_pagesのモック
        mock_page = MagicMock(spec=LTPage)
        mock_page.height = 842

        text1 = MagicMock(spec=LTTextContainer)
        text1.get_text.return_value = "No.1"
        text1.y0, text1.y1 = 480, 500

        text2 = MagicMock(spec=LTTextContainer)
        text2.get_text.return_value = "No.2"
        text2.y0, text2.y1 = 280, 300

        mock_page.__iter__.return_value = [text1, text2]
        mocker.patch(
            "src.core.image_processor.extract_pages",
            return_value=[mock_page],
        )

        # テスト実行
        regions = processor.extract_detail_regions(sample_pdf_path)

        # 結果の検証
        assert len(regions) == 2
        assert regions[0].no == "1"
        assert regions[1].no == "2"

    @pytest.mark.asyncio
    async def test_extract_detail_images(
        self, processor, sample_pdf_path, sample_image, tmp_path, mocker
    ):
        """明細画像の抽出テスト"""
        # PyMuPDFのモック
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_pixmap = MagicMock()

        mock_pdf.__len__.return_value = 1
        mock_pdf.__getitem__.return_value = mock_page
        mock_page.get_pixmap.return_value = mock_pixmap
        mock_pixmap.width = 800
        mock_pixmap.height = 1000
        mock_pixmap.samples = sample_image.tobytes()

        mocker.patch("fitz.open", return_value=mock_pdf)

        # テスト用のディレクトリ
        output_dir = tmp_path / "output"
        debug_dir = tmp_path / "debug"

        # テスト用の領域情報
        regions = [
            DetailRegion(
                page_num=1, no="1", y_top=500, y_bottom=400, x_left=50, x_right=750
            ),
            DetailRegion(
                page_num=1, no="2", y_top=300, y_bottom=200, x_left=50, x_right=750
            ),
        ]

        # テスト実行
        image_paths = processor.extract_detail_images(
            sample_pdf_path, regions, str(output_dir), str(debug_dir)
        )

        # 結果の検証
        assert len(image_paths) == 2
        assert all(os.path.exists(path) for path in image_paths)
        assert os.path.exists(debug_dir / "debug_page_1.jpg")

        # 生成された画像の検証
        for path in image_paths:
            img = Image.open(path)
            assert img.mode == "RGB"
            assert img.size[0] == 831  # (x_right - x_left) * scale_factor
            img.close()
