"""
ロギング機能のテスト
"""

import os
import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from logging.handlers import TimedRotatingFileHandler

from src.utils.logger import (
    CustomLogger,
    get_logger,
    LOG_FORMAT,
    DATE_FORMAT,
    BACKUP_COUNT,
    DEFAULT_LOG_LEVEL,
)


@pytest.fixture
def temp_log_dir(tmp_path):
    """テスト用の一時ログディレクトリを提供"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture(autouse=True)
def reset_logger():
    """各テストの前にロガーをリセット"""
    CustomLogger._instance = None
    yield
    CustomLogger._instance = None


@pytest.fixture
def mock_log_dir(temp_log_dir, monkeypatch):
    """ログディレクトリのパスをモック"""
    monkeypatch.setattr("src.utils.logger.LOG_DIR", temp_log_dir)
    monkeypatch.setattr(
        "src.utils.logger.LOG_FILE", temp_log_dir / "invoice_system.log"
    )
    return temp_log_dir


def test_logger_initialization(mock_log_dir, monkeypatch):
    """ロガーの初期化テスト"""
    # 環境変数をクリア
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    # ロガーの取得
    logger = get_logger("test_logger")

    # ロガーの基本設定の検証
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO  # デフォルトのログレベル

    # ハンドラーの検証
    handlers = logger.handlers
    assert len(handlers) == 3  # ファイル、コンソール、エラーの3つのハンドラー

    # 各ハンドラーの検証
    handler_types = [type(h) for h in handlers]
    assert TimedRotatingFileHandler in handler_types  # ファイルハンドラー
    assert logging.StreamHandler in handler_types  # コンソールハンドラー

    # ファイルの作成を確認
    log_file = mock_log_dir / "invoice_system.log"
    error_log_file = mock_log_dir / "error.log"
    assert log_file.exists()
    assert error_log_file.exists()


def test_log_format(mock_log_dir):
    """ログフォーマットのテスト"""
    logger = get_logger("test_format")

    # ファイルハンドラーのフォーマットを検証
    file_handler = next(
        h for h in logger.handlers if isinstance(h, TimedRotatingFileHandler)
    )
    assert file_handler.formatter._fmt == LOG_FORMAT
    assert file_handler.formatter.datefmt == DATE_FORMAT


def test_log_levels(mock_log_dir, monkeypatch):
    """ログレベルのテスト"""
    # 環境変数でログレベルを設定
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    CustomLogger._instance = None  # ロガーをリセット
    logger = get_logger("test_levels")
    assert logger.level == DEFAULT_LOG_LEVEL

    # 無効なログレベル
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    CustomLogger._instance = None  # ロガーをリセット
    logger = get_logger("test_invalid_level")
    assert logger.level == logging.INFO  # デフォルトに戻る


def test_file_handler_rotation(mock_log_dir):
    """ファイルローテーションのテスト"""
    logger = get_logger("test_rotation")
    file_handler = next(
        h for h in logger.handlers if isinstance(h, TimedRotatingFileHandler)
    )

    # ローテーション設定の検証
    assert (
        file_handler.when.lower() == "midnight"
    )  # 日次ローテーション（大文字小文字を区別しない）
    assert file_handler.interval == 1  # 1日ごと
    assert file_handler.backupCount == BACKUP_COUNT  # バックアップ数
    assert file_handler.encoding == "utf-8-sig"  # Windows対応のエンコーディング


def test_error_handler(mock_log_dir):
    """エラーハンドラーのテスト"""
    logger = get_logger("test_error")
    error_handler = next(
        h
        for h in logger.handlers
        if isinstance(h, TimedRotatingFileHandler) and h.level == logging.ERROR
    )

    # エラーハンドラーの設定を検証
    assert error_handler.baseFilename.endswith("error.log")
    assert error_handler.level == logging.ERROR


def test_singleton_behavior():
    """シングルトンパターンのテスト"""
    # 同じ名前で2回ロガーを取得
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")

    # 同じインスタンスであることを確認
    assert logger1 is logger2
    assert CustomLogger._instance is logger1


def test_permission_error(mock_log_dir):
    """権限エラーのテスト"""
    # ログディレクトリを作成
    mock_log_dir.mkdir(parents=True, exist_ok=True)
    log_file = mock_log_dir / "invoice_system.log"

    # ログファイルを作成して読み取り専用に設定
    log_file.touch()
    if os.name == "nt":
        import stat

        log_file.chmod(stat.S_IREAD)  # Windowsの場合
    else:
        log_file.chmod(0o444)  # UNIXの場合

    # ロガーをリセット
    CustomLogger._instance = None

    # ログファイルへの書き込みで権限エラー
    with pytest.raises(PermissionError):
        logger = get_logger("test_permission")
        logger.info("このメッセージは書き込めないはず")


def test_directory_creation_error(monkeypatch):
    """ディレクトリ作成エラーのテスト"""
    # 無効なパスを設定（Windowsで無効な文字を含むパス）
    invalid_dir = Path("invalid/path/*:<>/logs")
    monkeypatch.setattr("src.utils.logger.LOG_DIR", invalid_dir)

    # ロガーをリセット
    CustomLogger._instance = None

    # OSErrorの発生を確認
    with pytest.raises(OSError):
        logger = get_logger("test_dir_error")
        logger.info("このメッセージは書き込めないはず")


def test_log_output(mock_log_dir):
    """ログ出力のテスト"""
    # ログディレクトリを作成
    mock_log_dir.mkdir(parents=True, exist_ok=True)

    logger = get_logger("test_output")
    log_file = mock_log_dir / "invoice_system.log"
    error_log = mock_log_dir / "error.log"

    # 各レベルのログを出力
    logger.debug("デバッグメッセージ")
    logger.info("情報メッセージ")
    logger.warning("警告メッセージ")
    logger.error("エラーメッセージ")

    # ファイルが作成されるまで少し待つ
    import time

    time.sleep(0.1)

    # ログファイルの内容を検証
    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8-sig")
    assert "情報メッセージ" in log_content
    assert "警告メッセージ" in log_content
    assert "エラーメッセージ" in log_content

    # エラーログの内容を検証
    assert error_log.exists()
    error_content = error_log.read_text(encoding="utf-8-sig")
    assert "エラーメッセージ" in error_content
    assert "情報メッセージ" not in error_content  # INFO レベルは含まれない


def test_exception_logging(mock_log_dir):
    """例外ログのテスト"""
    logger = get_logger("test_exception")
    error_log = mock_log_dir / "error.log"

    try:
        raise ValueError("テストエラー")
    except ValueError:
        logger.exception("エラーが発生しました")

    # エラーログの内容を検証
    error_content = error_log.read_text(encoding="utf-8-sig")
    assert "エラーが発生しました" in error_content
    assert "ValueError: テストエラー" in error_content
    assert "Traceback" in error_content
