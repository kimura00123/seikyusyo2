from typing import List, Optional, Dict
from PIL import Image
import os
import re
from dataclasses import dataclass
import fitz
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTPage
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.utils.text_processing import is_detail_number

settings = get_settings()
logger = get_logger(__name__)

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
        self._page_images: Dict[int, Image.Image] = {}

    def _convert_pdf_pages_to_images(self, pdf_path: str) -> None:
        """PDFの全ページを画像に変換してキャッシュする"""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                # ページを画像として取得
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(self.dpi / 72, self.dpi / 72))
                
                # PILイメージに変換してキャッシュ
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                self._page_images[page_num] = img
                
            doc.close()
            logger.debug(f"PDFの全ページを画像に変換: {len(self._page_images)}ページ")
            
        except Exception as e:
            logger.error(f"PDFページの画像変換に失敗: {e}")
            raise

    def extract_detail_regions(self, pdf_path: str) -> List[DetailLine]:
        """PDFから明細行の位置情報を抽出する - シンプルなアプローチ"""
        logger.debug(f"明細行の位置情報抽出開始: {pdf_path}")
        detail_lines = []
        current_page = 0

        # PDFのページ高さを取得
        doc = fitz.open(pdf_path)
        pdf_height = doc[0].rect.height
        doc.close()

        for page_layout in extract_pages(pdf_path):
            if not isinstance(page_layout, LTPage):
                continue

            logger.debug(f"ページ {current_page + 1} の処理開始")
            
            # 明細番号とその位置を収集
            number_positions = []
            
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if not text:
                        continue
                    
                    # 明細番号の検出
                    detail_no = is_detail_number(text)
                    if detail_no:
                        logger.debug(f"明細番号を検出: No.{detail_no}, 位置: y1={element.y1}, y0={element.y0}")
                        # 明細番号とその上下の位置を記録
                        number_positions.append((detail_no, element.y1, element.y0))
            
            # 明細番号の位置でソート（上から下）
            number_positions.sort(key=lambda x: -x[1])
            
            # ページの余白
            page_top = page_layout.height
            page_bottom = 0
            
            # 各明細行の範囲を決定 - シンプルなアプローチ
            for i, (detail_no, y1, y0) in enumerate(number_positions):
                # 上端は現在の明細番号より少し上（余裕を持たせる）
                y_top = y1 + 15  # 15ポイント上
                
                # 下端の決定
                if i < len(number_positions) - 1:
                    # 次の明細番号がある場合は、その位置より少し下まで
                    next_y1 = number_positions[i + 1][1]
                    y_bottom = next_y1 - 15  # 15ポイント下
                else:
                    # ページ最後の明細の場合は、ページ下部まで
                    y_bottom = page_bottom
                
                # 範囲が負にならないように確認
                if y_bottom <= y_top:
                    y_bottom = y_top - 100  # 最低100ポイントは確保
                
                detail_lines.append(
                    DetailLine(
                        page_num=current_page,
                        no=detail_no,
                        y_top=y_top,
                        y_bottom=y_bottom,
                        x_left=40,
                        x_right=page_layout.width - 30,
                    )
                )
            
            current_page += 1
        
        return detail_lines

    def extract_customer_info(self, pdf_path: str) -> Dict[str, str]:
        """PDFから顧客情報を抽出する"""
        customer_info = {}
        
        for page_layout in extract_pages(pdf_path):
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    text = element.get_text().strip()
                    if re.match(r'^F\d+\s', text) and '_' not in text.split()[0]:
                        # 顧客コードを抽出 (例: "F015" など)
                        customer_code = text.split()[0]
                        customer_info[customer_code] = text
        
        return customer_info

    def extract_detail_image(self, pdf_path: str, detail_no: str, output_path: str) -> None:
        """明細行の画像を抽出する"""
        try:
            # 明細行の位置情報を取得
            detail_lines = self.extract_detail_regions(pdf_path)
            target_detail = next((d for d in detail_lines if d.no == detail_no), None)
            if not target_detail:
                raise Exception(f"明細番号 {detail_no} が見つかりません")

            logger.debug(f"明細行の抽出開始: detail_no={detail_no}")
            logger.debug(f"PDF path: {pdf_path}")
            logger.debug(f"Output path: {output_path}")
            logger.debug(f"Target detail: {target_detail}")

            # PDFを開く
            doc = fitz.open(pdf_path)
            page = doc[target_detail.page_num]
            pdf_height = page.rect.height
            logger.debug(f"PDF page size: {page.rect}")

            # PDFMinerの座標系（左下原点）からPyMuPDFの座標系（左上原点）に変換
            clip_rect = fitz.Rect(
                target_detail.x_left,
                pdf_height - target_detail.y_top,
                target_detail.x_right,
                pdf_height - target_detail.y_bottom
            )
            logger.debug(f"Clip rectangle: {clip_rect}")

            # 画像として抽出
            matrix = fitz.Matrix(self.dpi / 72, self.dpi / 72)
            logger.debug(f"Matrix scale: {self.dpi / 72}")
            pix = page.get_pixmap(matrix=matrix, clip=clip_rect)
            logger.debug(f"Extracted image size: {pix.width}x{pix.height}")

            # 画像を保存
            logger.debug(f"Saving image to: {output_path}")
            pix.save(output_path)
            logger.debug("Image saved successfully")

            doc.close()
            logger.debug("PDF closed")

        except Exception as e:
            raise Exception(f"画像抽出に失敗しました: {str(e)}")

    def extract_single_detail_image(
        self, 
        pdf_path: str, 
        detail_region: DetailLine, 
        output_path: str
    ) -> None:
        """単一の明細行の画像を抽出する"""
        try:
            logger.debug(f"単一明細行の抽出開始: detail_no={detail_region.no}")
            
            # キャッシュされた画像がない場合は変換
            if not self._page_images:
                self._convert_pdf_pages_to_images(pdf_path)
            
            # キャッシュから対象ページの画像を取得
            page_image = self._page_images.get(detail_region.page_num)
            if not page_image:
                raise Exception(f"ページ {detail_region.page_num} の画像が見つかりません")
            
            # スケール係数を計算
            scale_factor = page_image.height / self.pdf_height
            
            # 座標を画像のピクセル座標に変換
            x1 = int(detail_region.x_left * scale_factor)
            y1 = int((self.pdf_height - detail_region.y_top) * scale_factor)
            x2 = int(detail_region.x_right * scale_factor)
            y2 = int((self.pdf_height - detail_region.y_bottom) * scale_factor)
            
            # 画像を切り抜き
            detail_image = page_image.crop((x1, y1, x2, y2))
            
            # 出力ディレクトリの作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 画像を保存
            detail_image.save(output_path, quality=95)
            logger.debug(f"画像を保存: {output_path}")

        except Exception as e:
            logger.error(f"明細画像の抽出に失敗: {str(e)}")
            raise

    def cleanup(self):
        """キャッシュされた画像を解放"""
        for img in self._page_images.values():
            img.close()
        self._page_images.clear()