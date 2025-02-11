import os
from typing import List
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse
from core.pdf_parser import PDFParser
from core.structuring import StructuringEngine
from core.validation import Validator
from core.image_processor import ImageProcessor
from core.excel_exporter import ExcelExporter
from utils.logger import get_logger
from utils.config import Config
from utils.temp_file_manager import TempFileManager

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    PDFファイルをアップロードして処理する

    Args:
        file (UploadFile): アップロードされたPDFファイル

    Returns:
        dict: 処理結果
    """
    try:
        # 一時ディレクトリの準備
        temp_dir = Config.get_temp_dir()
        upload_dir = temp_dir / "uploads"
        image_dir = temp_dir / "images"
        processed_dir = temp_dir / "processed"

        for directory in [upload_dir, image_dir, processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # PDFファイルの保存
        pdf_path = upload_dir / file.filename
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        logger.info(f"PDFファイルを保存: {pdf_path}")

        # PDFの解析
        parser = PDFParser()
        text_elements = parser.extract_text_with_positions(str(pdf_path))

        # 構造化処理
        engine = StructuringEngine()
        structured_data = await engine.structure_invoice(text_elements)

        # バリデーション
        validator = Validator()
        validation_result = validator.validate(structured_data)

        if not validation_result.is_valid:
            return {
                "status": "error",
                "message": "バリデーションエラー",
                "errors": [
                    {"field": e.field, "message": e.message}
                    for e in validation_result.errors
                ],
            }

        # 明細画像の抽出
        image_processor = ImageProcessor()
        regions = image_processor.extract_detail_regions(str(pdf_path))
        image_paths = image_processor.extract_detail_images(
            str(pdf_path), regions, str(image_dir)
        )

        # エクセルファイルの出力
        exporter = ExcelExporter()
        excel_path = exporter.export_to_excel(
            validation_result.normalized_data,
            str(processed_dir),
            f"processed_{file.filename}.xlsx",
        )

        return {
            "status": "success",
            "message": "処理が完了しました",
            "data": {
                "pdf_filename": file.filename,
                "excel_path": str(excel_path),
                "image_count": len(image_paths),
                "warnings": [
                    {"field": w.field, "message": w.message}
                    for w in validation_result.warnings
                ],
            },
        }

    except Exception as e:
        logger.error(f"ドキュメント処理でエラー: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
    処理済みファイルをダウンロードする

    Args:
        filename (str): ダウンロードするファイル名

    Returns:
        FileResponse: ファイルのレスポンス
    """
    try:
        processed_dir = Config.get_temp_dir() / "processed"
        file_path = processed_dir / filename

        if not file_path.exists():
            return {"status": "error", "message": "ファイルが見つかりません"}

        return FileResponse(
            str(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )

    except Exception as e:
        logger.error(f"ファイルダウンロードでエラー: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.get("/cleanup")
async def cleanup_temp_files():
    """
    一時ファイルのクリーンアップを実行する

    Returns:
        dict: クリーンアップ結果
    """
    try:
        temp_manager = TempFileManager(str(Config.get_temp_dir()))
        deleted_count = temp_manager.cleanup_old_files(max_age_hours=24)

        return {
            "status": "success",
            "message": f"{deleted_count}件のファイルを削除しました",
        }

    except Exception as e:
        logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
