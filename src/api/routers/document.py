import os
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Path, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from src.core.pdf_parser import PDFParser
from src.core.structuring import StructuringEngine
from src.core.validation import Validator
from src.core.image_processor import ImageProcessor
from src.core.excel_exporter import ExcelExporter
from src.utils.logger import get_logger
from src.utils.config import settings
from src.utils.temp_file_manager import TempFileManager


# レスポンスモデルの定義
class ValidationError(BaseModel):
    field: str
    message: str


class ValidationWarning(BaseModel):
    field: str
    message: str


class ValidationResponse(BaseModel):
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationWarning] = []


class ProcessingStatus(BaseModel):
    status: str
    progress: int
    message: str
    errors: List[str] = []


router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", status_code=202)
async def upload_document(request: Request, file: UploadFile = File(...)):
    """
    PDFファイルをアップロードして処理する

    Args:
        request (Request): リクエストオブジェクト
        file (UploadFile): アップロードされたPDFファイル

    Returns:
        dict: 処理結果
    """
    try:
        # 一時ディレクトリの準備
        temp_dir = settings.TEMP_DIR
        upload_dir = temp_dir / "uploads"
        image_dir = temp_dir / "images"
        processed_dir = temp_dir / "processed"

        for directory in [upload_dir, image_dir, processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # ファイル名のバリデーション
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="PDFファイルのみアップロード可能です"
            )

        # 一意のドキュメントIDを生成
        document_id = f"{os.urandom(4).hex()}_{file.filename}"

        # 処理状態の初期化
        if not hasattr(request.app.state, "processing_status"):
            request.app.state.processing_status = {}
        request.app.state.processing_status[document_id] = {
            "status": "uploading",
            "progress": 0,
            "message": "ファイルをアップロード中",
            "errors": [],
        }

        try:
            # PDFファイルの保存
            pdf_path = upload_dir / document_id
            contents = await file.read()
            with open(pdf_path, "wb") as f:
                f.write(contents)

            logger.info(f"PDFファイルを保存: {pdf_path}")

            # 処理状態の更新
            request.app.state.processing_status[document_id]["status"] = "processing"
            request.app.state.processing_status[document_id]["progress"] = 10
            request.app.state.processing_status[document_id][
                "message"
            ] = "PDFの解析を開始"
            # PDFの解析
            parser = PDFParser()
            text_elements = parser.extract_text_with_positions(str(pdf_path))
            request.app.state.processing_status[document_id]["progress"] = 30
            request.app.state.processing_status[document_id][
                "message"
            ] = "テキスト抽出完了"

            # 構造化処理
            engine = StructuringEngine()
            structured_data = await engine.structure_invoice(text_elements)
            request.app.state.processing_status[document_id]["progress"] = 50
            request.app.state.processing_status[document_id][
                "message"
            ] = "構造化処理完了"

            # バリデーション
            validator = Validator()
            validation_result = validator.validate(structured_data, document_id)
            request.app.state.processing_status[document_id]["progress"] = 70
            request.app.state.processing_status[document_id][
                "message"
            ] = "バリデーション完了"

            # バリデーション結果を記録（エラーがあっても処理は継続）
            if not validation_result.is_valid:
                request.app.state.processing_status[document_id][
                    "status"
                ] = "has_validation_errors"
                request.app.state.processing_status[document_id]["errors"] = [
                    f"{e.field}: {e.message}" for e in validation_result.errors
                ]
                logger.warning(f"バリデーションエラーを検出: {document_id}")

            # 明細画像の抽出
            image_processor = ImageProcessor()
            regions = image_processor.extract_detail_regions(str(pdf_path))
            image_paths = image_processor.extract_detail_images(
                str(pdf_path), regions, str(image_dir / document_id)
            )
            request.app.state.processing_status[document_id]["progress"] = 90
            request.app.state.processing_status[document_id]["message"] = "画像抽出完了"

            # エクセルファイルの出力
            exporter = ExcelExporter()
            excel_path = exporter.export_to_excel(
                structured_data,  # normalized_dataの代わりにstructured_dataを使用
                str(processed_dir),
                f"{document_id}.xlsx",
            )
            request.app.state.processing_status[document_id]["progress"] = 100
            request.app.state.processing_status[document_id]["status"] = "completed"
            request.app.state.processing_status[document_id]["message"] = "処理完了"

            logger.info(f"ドキュメント処理完了: {document_id}")
            # レスポンスデータの作成
            response_data = {
                "status": "success",
                "message": "処理が完了しました",
                "document_id": document_id,
                "data": {
                    "pdf_filename": file.filename,
                    "excel_path": str(excel_path),
                    "image_count": len(image_paths),
                    "structured_data": structured_data,  # 辞書オブジェクトをそのまま使用
                },
                "validation_results": {
                    "is_valid": validation_result.is_valid,
                    "items": [
                        {
                            "field": e.field,
                            "value": getattr(
                                e, "value", None
                            ),  # valueが存在しない場合はNone
                            "is_valid": False,
                            "message": e.message,
                        }
                        for e in validation_result.errors
                    ]
                    + [
                        {
                            "field": w.field,
                            "value": getattr(
                                w, "value", None
                            ),  # valueが存在しない場合はNone
                            "is_valid": True,
                            "message": w.message,
                            "severity": "warning",
                        }
                        for w in validation_result.warnings
                    ],
                },
            }

            return JSONResponse(
                status_code=202,
                content=response_data,
            )

        except Exception as e:
            logger.error(
                f"ドキュメント処理でエラー: {document_id} - {e}", exc_info=True
            )
            if document_id in request.app.state.processing_status:
                request.app.state.processing_status[document_id]["status"] = "error"
                request.app.state.processing_status[document_id][
                    "message"
                ] = "処理エラー"
                request.app.state.processing_status[document_id]["errors"].append(
                    str(e)
                )
            raise HTTPException(
                status_code=500,
                detail=f"ドキュメント処理でエラーが発生しました: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期せぬエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"予期せぬエラーが発生しました: {str(e)}"
        )


@router.get("/status/{document_id}")
async def get_processing_status(
    request: Request, document_id: str = Path(..., description="ドキュメントID")
) -> ProcessingStatus:
    """処理状態を取得する"""
    if (
        not hasattr(request.app.state, "processing_status")
        or document_id not in request.app.state.processing_status
    ):
        raise HTTPException(
            status_code=404, detail="指定されたドキュメントが見つかりません"
        )

    status_data = request.app.state.processing_status[document_id]
    logger.info(f"処理状態を取得: {document_id} - {status_data['status']}")
    return ProcessingStatus(**status_data)


@router.get("/validation/{document_id}")
async def get_validation_result(
    document_id: str = Path(..., description="ドキュメントID")
) -> ValidationResponse:
    """バリデーション結果を取得する"""
    try:
        # バリデーション結果の取得
        validator = Validator()
        result = validator.get_validation_result(document_id)

        if result is None:
            raise HTTPException(
                status_code=404, detail="バリデーション結果が見つかりません"
            )

        logger.info(f"バリデーション結果を取得: {document_id}")
        return ValidationResponse(**result)

    except Exception as e:
        logger.error(f"バリデーション結果の取得でエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"バリデーション結果の取得でエラーが発生しました: {str(e)}",
        )


@router.get("/images/{document_id}")
async def get_detail_images(
    document_id: str = Path(..., description="ドキュメントID"),
    page: Optional[int] = Query(None, description="ページ番号"),
) -> List[str]:
    """明細画像のパスリストを取得する"""
    try:
        image_dir = settings.TEMP_DIR / "images" / document_id
        if not image_dir.exists():
            raise HTTPException(status_code=404, detail="画像が見つかりません")

        # 画像パスのリストを取得
        image_paths = []
        for image_path in image_dir.glob("*.jpg"):
            if page is None or f"page{page}_" in image_path.name:
                image_paths.append(str(image_path))

        logger.info(f"明細画像のパスを取得: {document_id}, {len(image_paths)}件")
        return image_paths

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"画像パスの取得でエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"画像パスの取得でエラーが発生しました: {str(e)}"
        )


@router.get("/download/{document_id}")
async def download_file(document_id: str = Path(..., description="ドキュメントID")):
    """
    処理済みファイルをダウンロードする

    Args:
        filename (str): ダウンロードするファイル名

    Returns:
        FileResponse: ファイルのレスポンス
    """
    try:
        # 処理済みファイルの取得
        processed_dir = settings.TEMP_DIR / "processed"
        file_path = processed_dir / f"{document_id}.xlsx"

        if not file_path.exists():
            logger.warning(f"ダウンロードファイルが見つかりません: {document_id}")
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")

        logger.info(f"ファイルのダウンロード: {document_id}")
        return FileResponse(
            str(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"processed_{document_id}.xlsx",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"ファイルダウンロードでエラー: {document_id} - {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"ファイルダウンロードでエラーが発生しました: {str(e)}",
        )


@router.post("/cleanup")
async def cleanup_temp_files(
    max_age: Optional[int] = Query(24, description="削除する経過時間（時間単位）")
):
    """
    一時ファイルのクリーンアップを実行する

    Returns:
        dict: クリーンアップ結果
    """
    try:
        # 一時ファイルのクリーンアップ
        temp_manager = TempFileManager(str(settings.TEMP_DIR))
        deleted_count = temp_manager.cleanup_old_files(max_age_hours=max_age)
        logger.info(f"一時ファイルのクリーンアップ完了: {deleted_count}件")

        return JSONResponse(
            content={
                "status": "success",
                "message": f"{deleted_count}件のファイルを削除しました",
            }
        )

    except Exception as e:
        logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"クリーンアップでエラーが発生しました: {str(e)}"
        )
