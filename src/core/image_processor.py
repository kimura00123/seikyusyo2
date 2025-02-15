import os
import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LTPage,
    LTTextContainer,
    LTChar,
    LTTextLineHorizontal,
    LTTextBoxHorizontal,
)
from utils.logger import get_logger
from utils.config import settings

logger = get_logger(__name__)


@dataclass
class DetailRegion:
    """明細行の領域情報"""

    page_num: int
    no: str
    y_top: float
    y_bottom: float
    description: str = ""
    x_left: float = 40
    x_right: float = 800


class ImageProcessor:
    """画像処理エンジン"""

    def __init__(self):
        # 画像設定
        self.dpi = settings.IMAGE_DPI
        self.quality = settings.IMAGE_QUALITY
        self.pdf_height = 842  # A4サイズの高さ（ポイント単位）

    def extract_detail_regions(self, pdf_path: str) -> List[DetailRegion]:
        """
        PDFから明細行の位置情報を抽出する

        Args:
            pdf_path (str): PDFファイルのパス

        Returns:
            List[DetailRegion]: 明細行の領域情報リスト
        """
        try:
            detail_regions = []
            current_page = 0

            for page_layout in extract_pages(pdf_path):
                if not isinstance(page_layout, LTPage):
                    continue

                current_page += 1
                logger.info(f"ページ {current_page} の明細行を抽出中")

                # 明細番号とその位置を収集
                number_positions = self._collect_detail_numbers(page_layout)

                # 各明細行の範囲を決定
                page_regions = self._determine_detail_regions(
                    number_positions, page_layout.height, current_page
                )
                detail_regions.extend(page_regions)

            logger.info(f"明細行の抽出が完了: {len(detail_regions)}件")
            return detail_regions

        except Exception as e:
            logger.error(f"明細行の抽出でエラー: {e}", exc_info=True)
            raise

    def extract_detail_images(
        self,
        pdf_path: str,
        regions: List[DetailRegion],
        output_dir: str,
        debug_dir: Optional[str] = None,
    ) -> List[str]:
        """
        PDFから明細行の画像を抽出する

        Args:
            pdf_path (str): PDFファイルのパス
            regions (List[DetailRegion]): 明細行の領域情報リスト
            output_dir (str): 出力ディレクトリのパス
            debug_dir (Optional[str]): デバッグ用画像の出力ディレクトリ

        Returns:
            List[str]: 生成された画像ファイルのパスリスト
        """
        try:
            # 出力ディレクトリの作成
            os.makedirs(output_dir, exist_ok=True)
            if debug_dir:
                os.makedirs(debug_dir, exist_ok=True)

            # PDFを開く
            pdf_doc = fitz.open(pdf_path)
            image_paths = []

            for page_num in range(len(pdf_doc)):
                # このページの明細を抽出
                page_regions = [r for r in regions if r.page_num == page_num + 1]
                if not page_regions:
                    continue

                # ページを画像として取得
                page = pdf_doc[page_num]
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(self.dpi / 72.0, self.dpi / 72.0)
                )

                # PILイメージに変換
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # スケール係数を計算
                scale_factor = img.height / self.pdf_height

                # 明細行の切り出しと保存
                page_paths = self._process_page_details(
                    img,
                    page_regions,
                    scale_factor,
                    output_dir,
                    page_num + 1,
                    debug_dir,
                )
                image_paths.extend(page_paths)

            pdf_doc.close()
            logger.info(f"明細画像の抽出が完了: {len(image_paths)}件")
            return image_paths

        except Exception as e:
            logger.error(f"明細画像の抽出でエラー: {e}", exc_info=True)
            raise

    def _collect_detail_numbers(
        self, page_layout: LTPage
    ) -> List[Tuple[str, float, float]]:
        """
        ページ内の明細番号とその位置を収集する

        Args:
            page_layout (LTPage): ページのレイアウト情報

        Returns:
            List[Tuple[str, float, float]]: 明細番号、上端位置、下端位置のタプルリスト
        """
        number_positions = []

        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                detail_no = self._is_detail_number(text)
                if detail_no:
                    number_positions.append((detail_no, element.y1, element.y0))

        # 上から下に並べ替え
        return sorted(number_positions, key=lambda x: -x[1])

    def _is_detail_number(self, text: str) -> Optional[str]:
        """
        テキストが明細番号かどうかを判定する

        Args:
            text (str): 判定対象のテキスト

        Returns:
            Optional[str]: 明細番号。明細番号でない場合はNone
        """
        patterns = [r"^No\.\s*(\d+)\s*$", r"^\s*(\d+)\s*$"]  # No.10 or No10  # 10
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _determine_detail_regions(
        self,
        number_positions: List[Tuple[str, float, float]],
        page_height: float,
        page_num: int,
    ) -> List[DetailRegion]:
        """
        明細行の範囲を決定する

        Args:
            number_positions (List[Tuple[str, float, float]]): 明細番号の位置情報
            page_height (float): ページの高さ
            page_num (int): ページ番号

        Returns:
            List[DetailRegion]: 明細行の領域情報リスト
        """
        regions = []
        margin = 10  # マージン（ポイント単位）

        for i, (no, y_top, y_bottom) in enumerate(number_positions):
            # 次の明細行までを範囲とする
            if i < len(number_positions) - 1:
                next_y_top = number_positions[i + 1][1]
            else:
                next_y_top = 0  # ページの最下部まで

            # マージンを考慮した範囲を設定
            region = DetailRegion(
                page_num=page_num,
                no=no,
                y_top=min(y_top + margin, page_height),
                y_bottom=max(next_y_top - margin, 0),
            )
            regions.append(region)

        return regions

    def _process_page_details(
        self,
        page_image: Image.Image,
        regions: List[DetailRegion],
        scale_factor: float,
        output_dir: str,
        page_num: int,
        debug_dir: Optional[str] = None,
    ) -> List[str]:
        """
        ページ内の明細行を処理する

        Args:
            page_image (Image.Image): ページの画像
            regions (List[DetailRegion]): 明細行の領域情報リスト
            scale_factor (float): スケール係数
            output_dir (str): 出力ディレクトリのパス
            page_num (int): ページ番号
            debug_dir (Optional[str]): デバッグ用画像の出力ディレクトリ

        Returns:
            List[str]: 生成された画像ファイルのパスリスト
        """
        image_paths = []

        if debug_dir:
            debug_image = page_image.copy()
            debug_draw = ImageDraw.Draw(debug_image)

        for region in regions:
            # 座標変換
            x_left = int(region.x_left * scale_factor)
            x_right = int(region.x_right * scale_factor)
            y_top = int((self.pdf_height - region.y_top) * scale_factor)
            y_bottom = int((self.pdf_height - region.y_bottom) * scale_factor)

            # 明細行の切り出し
            detail_image = page_image.crop((x_left, y_top, x_right, y_bottom))

            # 画像の保存
            output_path = os.path.join(
                output_dir, f"page{page_num}_detail{region.no}.jpg"
            )
            detail_image.save(output_path, "JPEG", quality=self.quality)
            image_paths.append(output_path)

            # デバッグ用の範囲表示
            if debug_dir:
                debug_draw.rectangle(
                    [(x_left, y_top), (x_right, y_bottom)], outline="red", width=2
                )
                debug_draw.text((x_left + 5, y_top + 5), f"No.{region.no}", fill="red")

        # デバッグ画像の保存
        if debug_dir:
            debug_path = os.path.join(debug_dir, f"debug_page_{page_num}.jpg")
            debug_image.save(debug_path, "JPEG", quality=self.quality)

        return image_paths


# 使用例:
"""
processor = ImageProcessor()

# 明細行の位置情報を抽出
regions = processor.extract_detail_regions("invoice.pdf")

# 明細画像を抽出
image_paths = processor.extract_detail_images(
    "invoice.pdf",
    regions,
    "output/images",
    "output/debug"  # デバッグ画像を出力する場合
)
"""
