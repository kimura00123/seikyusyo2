import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# ログフォーマットの設定
LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ログファイルの設定
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "invoice_system.log"
BACKUP_COUNT = 7  # 7日分のログを保持

# ログレベルの設定
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,  # 開発時の詳細情報
    "INFO": logging.INFO,  # 通常の操作ログ
    "WARNING": logging.WARNING,  # 警告（軽度の問題）
    "ERROR": logging.ERROR,  # エラー（重大な問題）
    "CRITICAL": logging.CRITICAL,  # 致命的なエラー
}

# 環境変数からログレベルを取得（デフォルトはINFO）
DEFAULT_LOG_LEVEL = LOG_LEVELS.get(os.getenv("LOG_LEVEL", "INFO"), logging.INFO)


class CustomLogger:
    """カスタムロガークラス"""

    _instance: Optional[logging.Logger] = None

    @classmethod
    def setup_logger(cls, name: str) -> logging.Logger:
        """
        ロガーを設定する

        Args:
            name (str): ロガー名

        Returns:
            logging.Logger: 設定済みのロガー

        Raises:
            OSError: ログファイルの作成に失敗した場合
            PermissionError: ログファイルへの書き込み権限がない場合
        """
        if cls._instance is not None:
            return cls._instance

        # ロガーの作成
        logger = logging.getLogger(name)
        logger.setLevel(DEFAULT_LOG_LEVEL)

        try:
            # ログディレクトリの作成
            LOG_DIR.mkdir(parents=True, exist_ok=True)

            # ファイルハンドラーの設定（日次ローテーション）
            file_handler = TimedRotatingFileHandler(
                LOG_FILE,
                when="midnight",  # 日次でローテーション
                interval=1,  # 1日ごと
                backupCount=BACKUP_COUNT,
                encoding="utf-8-sig",  # Windows対応のためBOM付きUTF-8を使用
            )
            file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # コンソールハンドラーの設定
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # エラーハンドラーの設定（エラーレベル以上を別ファイルに記録）
            error_handler = TimedRotatingFileHandler(
                LOG_DIR / "error.log",
                when="midnight",
                interval=1,
                backupCount=BACKUP_COUNT,
                encoding="utf-8-sig",
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            logger.addHandler(error_handler)

        except PermissionError as e:
            print(f"ログファイルへのアクセス権限がありません: {e}", file=sys.stderr)
            raise
        except OSError as e:
            print(f"ログファイルの作成に失敗しました: {e}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"ログ設定で予期せぬエラーが発生しました: {e}", file=sys.stderr)
            raise

        cls._instance = logger
        return logger


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得する

    Args:
        name (str): ロガー名

    Returns:
        logging.Logger: ロガーインスタンス
    """
    return CustomLogger.setup_logger(name)


# 使用例:
"""
logger = get_logger(__name__)

try:
    # 処理開始
    logger.info("処理を開始します")
    
    # デバッグ情報
    logger.debug("詳細なデバッグ情報")
    
    # 警告
    logger.warning("警告: 処理に時間がかかっています")
    
    # エラー（スタックトレース付き）
    logger.error("エラーが発生しました", exc_info=True)
    
    # 処理完了
    logger.info("処理が完了しました")

except Exception as e:
    # 重大なエラー
    logger.critical("致命的なエラーが発生しました", exc_info=True)
    raise
"""
