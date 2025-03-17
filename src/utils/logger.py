import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .config import get_settings

class CustomFormatter(logging.Formatter):
    """カスタムログフォーマッター（文字化け対策）"""
    
    def __init__(self, fmt: Optional[str] = None):
        super().__init__(fmt or self.default_format())
        self.encoding = 'utf-8'

    @staticmethod
    def default_format() -> str:
        return (
            "%(asctime)s [%(levelname)s] "
            "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )

    def formatException(self, ei) -> str:
        """例外情報のフォーマット（文字化け対策）"""
        result = super().formatException(ei)
        return repr(result)

class SensitiveFilter(logging.Filter):
    """機密情報除外フィルター"""
    
    def __init__(self):
        super().__init__()
        # 除外すべき機密情報のパターン
        self.patterns = [
            'api_key',
            'password',
            'secret',
            'token',
            'auth',
            'credit_card',
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """機密情報を'[FILTERED]'に置換"""
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern in self.patterns:
                if pattern in msg.lower():
                    # 機密情報を含む部分を[FILTERED]に置換
                    record.msg = '[FILTERED]'
                    break
        return True

class LogManager:
    """ログ管理クラス"""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_log_directory()
        self.logger = self._setup_logger()

    def _setup_log_directory(self) -> None:
        """ログディレクトリの設定"""
        log_dir = Path(self.settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logger(self) -> logging.Logger:
        """ロガーの設定"""
        logger = logging.getLogger('invoice_processor')
        logger.setLevel(self.settings.LOG_LEVEL)  # 環境変数のログレベル

        # 既存のハンドラをクリア
        logger.handlers.clear()

        # ファイルハンドラの設定（ローテーション付き）
        file_handler = self._setup_file_handler()
        logger.addHandler(file_handler)

        # エラーログ用ファイルハンドラの設定
        error_handler = self._setup_error_handler()
        logger.addHandler(error_handler)

        # コンソールハンドラの設定
        console_handler = self._setup_console_handler()
        logger.addHandler(console_handler)

        # 機密情報除外フィルターの追加
        sensitive_filter = SensitiveFilter()
        logger.addFilter(sensitive_filter)

        return logger

    def _setup_file_handler(self) -> logging.Handler:
        """通常のファイルハンドラの設定"""
        log_file = Path(self.settings.LOG_DIR) / 'invoice_processor.log'
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8',
            delay=True
        )
        formatter = CustomFormatter()
        handler.setFormatter(formatter)
        handler.setLevel(self.settings.LOG_LEVEL)  # 環境変数のログレベル
        return handler

    def _setup_error_handler(self) -> logging.Handler:
        """エラーログ用ファイルハンドラの設定"""
        error_log_file = Path(self.settings.LOG_DIR) / 'error.log'
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=error_log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8',
            delay=True
        )
        formatter = CustomFormatter()
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR)  # ERRORレベル以上
        return handler

    def _setup_console_handler(self) -> logging.Handler:
        """コンソールハンドラの設定"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = CustomFormatter()
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)  # INFOレベル以上
        return handler

    def get_logger(self) -> logging.Logger:
        """ロガーの取得"""
        return self.logger

# シングルトンインスタンス
_log_manager: Optional[LogManager] = None

def get_logger(name: str = None) -> logging.Logger:
    """ロガーのグローバルアクセサ"""
    global _log_manager
    if _log_manager is None:
        _log_manager = LogManager()
    logger = _log_manager.get_logger()
    if name:
        logger = logger.getChild(name)
    return logger

# 使用例:
"""
logger = get_logger()

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
