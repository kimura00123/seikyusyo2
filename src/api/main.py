import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.utils.logger import get_logger
from src.utils.config import get_settings
from pydantic import ValidationError

from src.core.error_handler import ErrorHandlerMiddleware
from src.core.errors import ErrorCode, ErrorLevel
from src.api.routers import document, approval, admin
from src.startup import initialize_environment, cleanup_environment

# ロガーの設定
logger = get_logger(__name__)

# 設定の取得
settings = get_settings()

# 環境の初期化
initialize_environment()

# FastAPIアプリケーションの作成
app = FastAPI(
    title="請求書構造化システム",
    description="請求書PDFから情報を抽出し、構造化データを提供するシステム",
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

# エラーハンドラーミドルウェアの設定
error_middleware = ErrorHandlerMiddleware()

# ルーターの登録
app.include_router(document.router, prefix="/api/documents")
app.include_router(approval.router, prefix="/api/approvals")
app.include_router(admin.router, prefix="/api/admin")

# 静的ファイルを提供する設定
# 注意: これはすべてのルートをキャッチするため、最後に配置する必要がある
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

# 起動時の処理
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    try:
        logger.info("アプリケーションを起動しています...")
        # 環境の初期化（すでに実行済みだが、念のため）
        initialize_environment()
        logger.info("アプリケーションの起動が完了しました")
    except Exception as e:
        logger.error(f"起動処理でエラー: {e}", exc_info=True)

# 終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    try:
        logger.info("アプリケーションをシャットダウンしています...")
        # 環境のクリーンアップ
        cleanup_environment()
        logger.info("アプリケーションのシャットダウンが完了しました")
    except Exception as e:
        logger.error(f"終了処理でエラー: {e}", exc_info=True)

if __name__ == "__main__":
    import uvicorn

    host = "0.0.0.0"
    port = settings.PORT
    reload = settings.is_development()

    logger.info(f"サーバーを起動: {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)
