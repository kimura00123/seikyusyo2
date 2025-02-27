from typing import Dict, Any, Optional
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import FileResponse
from src.utils.logger import get_logger
from src.core.pdf_parser import PDFParser
from src.core.structuring import StructuringEngine
from src.core.validation import ValidationEngine
from src.core.image_processor import ImageProcessor
from src.core.excel_exporter import ExcelExporter
from src.utils.temp_manager import temp_manager
from src.utils.config import get_settings

# ロガーの設定
logger = get_logger(__name__)

router = APIRouter(tags=["documents"])

settings = get_settings()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, str]:
    """PDFファイルをアップロードし、処理を開始する"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDFファイルのみ対応しています")

    try:
        # 一時ファイルとして保存
        task_id = temp_manager.generate_task_id()
        pdf_path = temp_manager.save_upload(file, task_id)

        # 非同期処理を開始（実際の環境では非同期キューを使用）
        # ここではデモのため同期的に処理
        parser = PDFParser(pdf_path)
        text_content = parser.extract_text_with_positions()

        structurer = StructuringEngine(pdf_path, task_id)
        document = structurer.structure_invoice(text_content)

        # 結果を一時保存（辞書形式に変換）
        temp_manager.save_result(task_id, document.model_dump())

        return {"task_id": task_id}

    except Exception as e:
        logger.error(f"アップロード処理でエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status/{task_id}")
async def get_processing_status(task_id: str) -> Dict[str, Any]:
    """処理状態を取得する"""
    try:
        result = temp_manager.get_result(task_id)
        if result:
            return {"status": "completed", "result": result}
        return {"status": "processing"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.get("/validation/{task_id}")
async def get_validation_result(task_id: str) -> Dict[str, Any]:
    """バリデーション結果を取得する"""
    try:
        document = temp_manager.get_result(task_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        validator = ValidationEngine()
        result = validator.validate_invoice(document)
        # Pydanticモデルを辞書に変換して返す
        return result.model_dump()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{task_id}/{detail_no}")
async def get_detail_image(task_id: str, detail_no: str) -> FileResponse:
    """明細行の画像を取得する"""
    try:
        image_path = temp_manager.get_image_path(task_id, detail_no)
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(image_path)

    except Exception as e:
        logger.error(f"明細画像の取得でエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/excel/{task_id}")
async def download_excel(
    task_id: str, edited_details: Optional[Dict[str, Any]] = Body(None)
) -> FileResponse:
    """エクセルファイルをダウンロードする"""
    try:
        logger.info(f"エクセル出力開始: task_id={task_id}")
        if edited_details:
            logger.info(f"編集された値: {edited_details}")

        document = temp_manager.get_result(task_id)
        if not document:
            logger.error(f"Document not found: task_id={task_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        # 編集された値がある場合は、それを反映
        if edited_details:
            logger.info("編集された値を反映開始")
            for detail_no, edited_detail in edited_details.items():
                # 該当する明細を探して更新
                for customer in document["customers"]:
                    for entry in customer["entries"]:
                        if entry["no"] == detail_no:
                            logger.info(f"明細を更新: no={detail_no}")
                            logger.info(f"更新前: {entry}")
                            entry.update(edited_detail)
                            logger.info(f"更新後: {entry}")
                            break

        logger.info("エクセル出力処理開始")
        exporter = ExcelExporter()
        excel_path = temp_manager.get_excel_path(task_id)
        logger.info(f"出力先パス: {excel_path}")
        exporter.export(document, excel_path)
        logger.info("エクセル出力完了")

        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"invoice_data_{task_id}.xlsx",
        )

    except Exception as e:
        logger.error(f"エクセル出力でエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
