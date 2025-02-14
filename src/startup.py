import os
import sys
import logging
from pathlib import Path
from utils.logger import get_logger
from utils.config import Config

# プロジェクトルートディレクトリをPYTHONPATHに追加
project_root = Path(__file__).parent
sys.path.append(str(project_root))

logger = get_logger(__name__)


def setup_environment():
    """環境設定を行う"""
    try:
        # 一時ディレクトリの作成
        temp_dir = Config.get_temp_dir()
        upload_dir = temp_dir / "uploads"
        image_dir = temp_dir / "images"
        processed_dir = temp_dir / "processed"

        for directory in [temp_dir, upload_dir, image_dir, processed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"ディレクトリを作成: {directory}")

        # 環境変数の検証
        Config.validate()
        logger.info("環境変数の検証が完了")

        # ログレベルの設定
        log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        logger.info(f"ログレベルを設定: {Config.LOG_LEVEL}")

        # 開発環境の場合は追加の設定
        if Config.is_development():
            logger.info("開発環境で実行中")
            # 開発用の設定をここに追加

        return True

    except Exception as e:
        logger.error(f"環境設定でエラー: {e}", exc_info=True)
        return False


def cleanup_environment():
    """環境のクリーンアップを行う"""
    try:
        # 一時ファイルの削除
        from utils.temp_file_manager import TempFileManager

        temp_manager = TempFileManager(str(Config.get_temp_dir()))
        temp_manager.cleanup_old_files(max_age_hours=24)
        logger.info("一時ファイルのクリーンアップが完了")

        return True

    except Exception as e:
        logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
        return False


def main():
    """メイン処理"""
    try:
        # 環境設定
        if not setup_environment():
            logger.error("環境設定に失敗しました")
            sys.exit(1)

        # APIサーバーの起動
        import uvicorn

        host = "0.0.0.0"
        port = int(Config.get("PORT", "8000"))
        reload = Config.is_development()

        logger.info(f"APIサーバーを起動: {host}:{port}")
        uvicorn.run("api.main:app", host=host, port=port, reload=reload)

    except Exception as e:
        logger.error(f"アプリケーションの起動でエラー: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # 終了時のクリーンアップ
        cleanup_environment()


if __name__ == "__main__":
    main()
