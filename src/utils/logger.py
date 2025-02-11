import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ログフォーマットの設定
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ログファイルの設定
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "invoice_system.log"
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# ログレベルの設定
DEFAULT_LOG_LEVEL = logging.INFO


def setup_logger(name: str) -> logging.Logger:
    """
    ロガーを設定する

    Args:
        name (str): ロガー名

    Returns:
        logging.Logger: 設定済みのロガー
    """
    # ロガーの作成
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LOG_LEVEL)

    # ハンドラーが既に設定されている場合は追加しない
    if logger.handlers:
        return logger

    try:
        # ログディレクトリの作成
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # ファイルハンドラーの設定
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(file_handler)

        # コンソールハンドラーの設定
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(console_handler)

    except Exception as e:
        # ログ設定に失敗した場合は標準エラー出力に出力
        print(f"ログ設定でエラー: {e}", file=sys.stderr)
        raise

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得する

    Args:
        name (str): ロガー名

    Returns:
        logging.Logger: ロガーインスタンス
    """
    return setup_logger(name)


# 使用例:
"""
logger = get_logger(__name__)

try:
    # 処理
    logger.info("処理を開始")
    # ...
    logger.info("処理が完了")

except Exception as e:
    logger.error(f"エラーが発生: {e}", exc_info=True)
    raise
"""
