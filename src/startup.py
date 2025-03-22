import os
import sys
import logging
from pathlib import Path
from src.utils.logger import get_logger
from src.utils.config import get_settings
from src.utils.temp_manager import temp_manager

# プロジェクトルートディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent
sys.path.append(str(project_root))

logger = get_logger(__name__)
settings = get_settings()


def initialize_environment():
    """環境の初期化を行う"""
    try:
        logger.info("環境の初期化を開始")
        
        # 一時ディレクトリの設定
        temp_dir = settings.TEMP_DIR
        # 文字列の場合はPathオブジェクトに変換
        if isinstance(temp_dir, str):
            temp_dir = Path(temp_dir)
        
        temp_manager.temp_dir = temp_dir
        logger.info(f"一時ディレクトリを設定: {temp_manager.temp_dir}")
        
        # 古い一時ファイルのクリーンアップ
        cleanup_environment()
        
        logger.info("環境の初期化が完了")
        return True
        
    except Exception as e:
        logger.error(f"環境の初期化でエラー: {e}", exc_info=True)
        return False


def cleanup_environment():
    """環境のクリーンアップを行う"""
    try:
        # 一時ファイルの削除
        temp_manager.temp_dir = settings.TEMP_DIR
        
        # 設定から削除対象ファイルの経過時間を取得
        cleanup_hours = 24  # デフォルト: 24時間
        if hasattr(settings, 'CLEANUP_FILE_AGE_HOURS'):
            cleanup_hours = settings.CLEANUP_FILE_AGE_HOURS
            
        deleted_count = temp_manager.cleanup_old_files(hours=cleanup_hours)
        logger.info(f"一時ファイルのクリーンアップが完了: {deleted_count}件")
        return deleted_count
    except Exception as e:
        logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
        return 0


def main():
    """メイン処理"""
    try:
        # 環境設定
        if not initialize_environment():
            logger.error("環境の初期化に失敗しました")
            sys.exit(1)

        # APIサーバーの起動
        import uvicorn

        host = "0.0.0.0"
        port = settings.PORT
        reload = settings.is_development()

        logger.info(f"APIサーバーを起動: {host}:{port}")
        uvicorn.run(
            "src.api.main:app",  # アプリケーションをインポート文字列として指定
            host=host,
            port=port,
            reload=reload
        )

    except Exception as e:
        logger.error(f"アプリケーションの起動でエラー: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # 終了時のクリーンアップ
        cleanup_environment()


if __name__ == "__main__":
    main()
