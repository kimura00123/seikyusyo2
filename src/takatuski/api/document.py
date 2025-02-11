import os
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
from pathlib import Path
from ...core.pdf_parser import PDFParser
from ...core.structuring import StructuringEngine
from ...core.validation import Validator
from ...core.image_processor import ImageProcessor
from ...core.excel_exporter import ExcelExporter
from ...utils.logger import get_logger
from ...utils.config import Config
from ...utils.temp_file_manager import TempFileManager

# ロガーの設定
logger = get_logger(__name__)

# ルーターの作成
router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)

# 一時ファイル管理
temp_manager = TempFileManager(str(Config.get_temp_dir()))


@router.post("/upload")
@temp_manager
async def upload_document(
    file: UploadFile = File(...), temp_files: List[str] = None
) -> dict:
    """
    PDFファイルをアップロードし、構造化処理を実行する

    Args:
        file (UploadFile): アップロードされたPDFファイル
        temp_files (List[str]): 一時ファイルのパスリスト（デコレータから注入）

    Returns:
        dict: 処理結果
    """
    try:
        # ファイル形式の検証
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="PDFファイルのみアップロード可能です"
            )

        # ファイルサイズの検証
        content = await file.read()
        if len(content) > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ファイルサイズは{Config.MAX_FILE_SIZE / 1024 / 1024}MB以下である必要があります",
            )

        # 一時ファイルの保存
        temp_path = temp_manager.generate_temp_path(temp_manager.upload_dir, ".pdf")
        temp_files.append(temp_path)

        with open(temp_path, "wb") as buffer:
            buffer.write(content)
        logger.info(f"PDFファイルを保存: {temp_path}")

        # PDF解析
        parser = PDFParser()
        text_elements = parser.extract_text_with_positions(temp_path)
        logger.info("PDFの解析が完了")

        # 構造化処理
        engine = StructuringEngine()
        structured_data = await engine.structure_invoice(text_elements)
        logger.info("構造化処理が完了")

        # バリデーション
        validator = Validator()
        validation_result = validator.validate(structured_data)
        logger.info("バリデーションが完了")

        # 明細画像の抽出
        image_processor = ImageProcessor()
        regions = image_processor.extract_detail_regions(temp_path)
        image_paths = image_processor.extract_detail_images(
            temp_path,
            regions,
            str(temp_manager.image_dir),
            str(temp_manager.processed_dir) if Config.is_development() else None,
        )
        temp_files.extend(image_paths)
        logger.info(f"明細画像を抽出: {len(image_paths)}件")

        # エクセル出力
        exporter = ExcelExporter()
        excel_path = exporter.export_to_excel(
            validation_result.normalized_data,
            str(temp_manager.processed_dir / "output.xlsx"),
        )
        temp_files.append(excel_path)
        logger.info(f"エクセルファイルを出力: {excel_path}")

        return {
            "message": "ファイルの処理が完了しました",
            "filename": file.filename,
            "validation_result": validation_result.dict(),
            "image_count": len(image_paths),
            "excel_path": excel_path,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ファイル処理でエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="ファイルの処理中にエラーが発生しました"
        )


@router.get("/images/{image_id}")
async def get_detail_image(image_id: str) -> FileResponse:
    """
    明細画像を取得する

    Args:
        image_id (str): 画像ID（ファイル名）

    Returns:
        FileResponse: 画像ファイル
    """
    try:
        image_path = temp_manager.image_dir / f"{image_id}.jpg"
        if not image_path.exists():
            raise HTTPException(
                status_code=404, detail="指定された画像が見つかりません"
            )

        return FileResponse(
            str(image_path), media_type="image/jpeg", filename=f"{image_id}.jpg"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"画像取得でエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="画像の取得中にエラーが発生しました"
        )


@router.get("/excel/{filename}")
async def get_excel_file(filename: str) -> FileResponse:
    """
    エクセルファイルをダウンロードする

    Args:
        filename (str): ファイル名

    Returns:
        FileResponse: エクセルファイル
    """
    try:
        excel_path = temp_manager.processed_dir / filename
        if not excel_path.exists():
            raise HTTPException(
                status_code=404, detail="指定されたファイルが見つかりません"
            )

        return FileResponse(
            str(excel_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"エクセルファイル取得でエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="ファイルの取得中にエラーが発生しました"
        )


@router.post("/cleanup")
async def cleanup_temp_files(background_tasks: BackgroundTasks) -> dict:
    """
    一時ファイルのクリーンアップを実行する

    Args:
        background_tasks (BackgroundTasks): バックグラウンドタスク

    Returns:
        dict: 処理結果
    """
    try:
        # バックグラウンドでクリーンアップを実行
        background_tasks.add_task(temp_manager.cleanup_old_files, max_age_hours=24)
        return {"message": "クリーンアップタスクを開始しました"}

    except Exception as e:
        logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="クリーンアップ処理中にエラーが発生しました"
        )
