import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.utils.logger import get_logger
from src.utils.config import get_settings
from pydantic import ValidationError
import asyncio

from src.core.error_handler import ErrorHandlerMiddleware
from src.core.errors import ErrorCode, ErrorLevel
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
app.add_middleware(ErrorHandlerMiddleware)

# ルーターのインポートと登録（循環インポートを避けるため、ここでインポート）
from src.api.routers import document, approval
app.include_router(document.router, prefix="/api/documents")
app.include_router(approval.router, prefix="/api/approvals")
# app.include_router(admin.router, prefix="/api/admin")  # コメントアウト

# 静的ファイルを提供する設定
# 注意: これはすべてのルートをキャッチするため、最後に配置する必要がある
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="static")

# グローバル変数でタスクを管理
cleanup_task = None
shutdown_event = asyncio.Event()

async def periodic_cleanup():
    """定期的にクリーンアップを実行するバックグラウンドタスク"""
    cleanup_interval = 3600  # デフォルト: 1時間（3600秒）
    
    try:
        # 設定から間隔を取得（設定がある場合）
        if hasattr(settings, 'CLEANUP_INTERVAL_SECONDS'):
            cleanup_interval = settings.CLEANUP_INTERVAL_SECONDS
    except Exception as e:
        logger.warning(f"クリーンアップ間隔の設定読み込みでエラー: {e}")
    
    logger.info(f"定期クリーンアップタスクを開始: {cleanup_interval}秒間隔")
    
    while not shutdown_event.is_set():
        try:
            logger.info("定期クリーンアップを開始")
            deleted_count = cleanup_environment()
            logger.info(f"定期クリーンアップが完了: {deleted_count}件のファイルを削除")
            
            # 指定された間隔で待機（シャットダウンイベントをチェックしながら）
            for _ in range(cleanup_interval):
                if shutdown_event.is_set():
                    break
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"定期クリーンアップでエラー: {e}", exc_info=True)
            # エラー発生時も一定時間待機してから再試行（短い間隔）
            await asyncio.sleep(60)
    
    logger.info("定期クリーンアップタスクを終了")

# 起動時の処理
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    global cleanup_task
    
    try:
        logger.info("アプリケーションを起動しています...")
        # 環境の初期化（すでに実行済みだが、念のため）
        initialize_environment()
        
        # バックグラウンドタスクを開始
        cleanup_task = asyncio.create_task(periodic_cleanup())
        logger.info("バックグラウンドクリーンアップタスクを開始")
        
        logger.info("アプリケーションの起動が完了しました")
    except Exception as e:
        logger.error(f"起動処理でエラー: {e}", exc_info=True)

# 終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    global cleanup_task
    
    try:
        logger.info("アプリケーションをシャットダウンしています...")
        
        # シャットダウンイベントをセット
        shutdown_event.set()
        
        # タスクが存在する場合は終了を待機
        if cleanup_task:
            try:
                # 最大10秒待機
                await asyncio.wait_for(cleanup_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("クリーンアップタスクの終了がタイムアウトしました")
            except Exception as e:
                logger.error(f"クリーンアップタスクの終了でエラー: {e}", exc_info=True)
        
        # 環境のクリーンアップ
        cleanup_environment()
        logger.info("アプリケーションのシャットダウンが完了しました")
    except Exception as e:
        logger.error(f"終了処理でエラー: {e}", exc_info=True)

# 管理用エンドポイント（オプション）
@app.get("/api/maintenance/cleanup")
async def manual_cleanup():
    """手動でクリーンアップを実行するエンドポイント"""
    try:
        deleted_count = cleanup_environment()
        return {"status": "success", "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"手動クリーンアップでエラー: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    from pathlib import Path

    host = "0.0.0.0"
    port = settings.PORT
    reload = settings.is_development()
    
    # 証明書ファイルのパスを設定
    cert_file = Path("certs/cert.pem")
    key_file = Path("certs/key.pem")
    
    # 証明書ファイルが存在する場合はHTTPSで起動
    if cert_file.exists() and key_file.exists():
        logger.info(f"HTTPSサーバーを起動: {host}:{port}")
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            reload=reload,
            ssl_keyfile=str(key_file),
            ssl_certfile=str(cert_file)
        )
    else:
        logger.info(f"HTTPサーバーを起動: {host}:{port} (証明書ファイルが見つからないためHTTPで起動)")
        uvicorn.run(app, host=host, port=port, reload=reload)