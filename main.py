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
from src.api.main import app as api_app

# ロガーの設定
logger = get_logger(__name__)

# 設定の取得
settings = get_settings()

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

# APIルーターをマウント
# 注意: すべてのAPIエンドポイントに /api プレフィックスを追加
app.mount("/api", api_app)

# 静的ファイルを提供する設定
# 注意: これはすべてのルートをキャッチするため、最後に配置する必要がある
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    host = "0.0.0.0"
    port = settings.PORT
    reload = settings.is_development()

    logger.info(f"サーバーを起動: {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=reload)