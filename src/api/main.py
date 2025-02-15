import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.utils.logger import get_logger
from src.utils.config import settings

# ロガーの設定
logger = get_logger(__name__)

# FastAPIアプリケーションの作成
app = FastAPI(
    title="請求書構造化システム API",
    description="請求書PDFから情報を抽出し、構造化データを提供するAPI",
    version="1.0.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    try:
        # 環境変数の検証
        settings.validate_production()
        logger.info("環境変数の検証が完了")

        # 一時ディレクトリの準備
        temp_dir = settings.TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"一時ディレクトリを作成: {temp_dir}")

        # ログレベルの設定
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        logger.info(f"ログレベルを設定: {settings.LOG_LEVEL}")

        # 開発環境の場合は追加の設定
        if settings.is_development():
            logger.info("開発環境で実行中")
            # 開発用の設定をここに追加

    except Exception as e:
        logger.error(f"起動処理でエラー: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    try:
        from src.utils.temp_file_manager import TempFileManager

        # 一時ファイルのクリーンアップ
        temp_manager = TempFileManager(str(settings.TEMP_DIR))
        deleted_count = temp_manager.cleanup_old_files(max_age_hours=24)
        logger.info(f"一時ファイルのクリーンアップが完了: {deleted_count}件")

    except Exception as e:
        logger.error(f"終了処理でエラー: {e}", exc_info=True)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    logger.error(f"予期せぬエラー: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "内部サーバーエラー",
            "detail": str(exc) if settings.is_development() else None,
        },
    )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


# ルーターの登録
from src.api.routers import document_router

app.include_router(
    document_router,
    prefix="/document",
    tags=["document"],
)


if __name__ == "__main__":
    import uvicorn

    host = "0.0.0.0"
    port = settings.PORT
    reload = settings.is_development()

    logger.info(f"APIサーバーを起動: {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)
