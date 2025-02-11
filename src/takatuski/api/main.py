from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from .routers import document
from utils.logger import get_logger
from utils.config import Config

# ロガーの設定
logger = get_logger(__name__)

# FastAPIアプリケーションの作成
app = FastAPI(
    title="Invoice Processing API",
    description="PDF請求書の構造化処理API",
    version="1.0.0",
)

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if Config.is_development() else ["https://your-production-domain.com"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 一時ディレクトリの作成
temp_dir = Config.get_temp_dir()
upload_dir = temp_dir / "uploads"
image_dir = temp_dir / "images"
processed_dir = temp_dir / "processed"

upload_dir.mkdir(exist_ok=True)
image_dir.mkdir(exist_ok=True)
processed_dir.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("アプリケーションを起動しています")
    logger.info(f"一時ディレクトリを初期化: {temp_dir}")

    # 環境変数の検証
    try:
        Config.validate()
        logger.info("環境変数の検証が完了しました")
    except ValueError as e:
        logger.error(f"環境変数の検証に失敗: {e}")
        if Config.is_production():
            raise


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("アプリケーションをシャットダウンしています")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException のハンドリング"""
    logger.error(f"HTTPエラーが発生: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外のハンドリング"""
    logger.error(f"予期せぬエラーが発生: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "内部サーバーエラー"},
    )


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": Config.APP_ENV,
    }


# ルーターの登録
app.include_router(document.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=Config.is_development(),
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
