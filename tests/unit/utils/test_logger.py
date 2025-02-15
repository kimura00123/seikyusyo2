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
)


@pytest.fixture
def temp_log_dir(tmp_path):
    """テスト用の一時ログディレクトリを提供"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def mock_log_dir(temp_log_dir, monkeypatch):
    """ログディレクトリのパスをモック"""
    monkeypatch.setattr("src.utils.logger.LOG_DIR", temp_log_dir)
    monkeypatch.setattr(
        "src.utils.logger.LOG_FILE", temp_log_dir / "invoice_system.log"
    )
    return temp_log_dir


def test_logger_initialization(mock_log_dir):
    """ロガーの初期化テスト"""
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
    logger = get_logger("test_levels")
    assert logger.level == logging.DEBUG

    # 無効なログレベル
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    logger = get_logger("test_invalid_level")
    assert logger.level == logging.INFO  # デフォルトに戻る


def test_file_handler_rotation(mock_log_dir):
    """ファイルローテーションのテスト"""
    logger = get_logger("test_rotation")
    file_handler = next(
        h for h in logger.handlers if isinstance(h, TimedRotatingFileHandler)
    )

    # ローテーション設定の検証
    assert file_handler.when == "midnight"  # 日次ローテーション
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
    # ログディレクトリの権限を変更（読み取り専用）
    mock_log_dir.chmod(0o444)

    # 権限エラーの発生を確認
    with pytest.raises(PermissionError):
        get_logger("test_permission")


def test_directory_creation_error(monkeypatch):
    """ディレクトリ作成エラーのテスト"""
    # 無効なパスを設定
    invalid_dir = Path("/invalid/path/logs")
    monkeypatch.setattr("src.utils.logger.LOG_DIR", invalid_dir)

    # OSErrorの発生を確認
    with pytest.raises(OSError):
        get_logger("test_dir_error")


def test_log_output(mock_log_dir):
    """ログ出力のテスト"""
    logger = get_logger("test_output")
    log_file = mock_log_dir / "invoice_system.log"
    error_log = mock_log_dir / "error.log"

    # 各レベルのログを出力
    logger.debug("デバッグメッセージ")
    logger.info("情報メッセージ")
    logger.warning("警告メッセージ")
    logger.error("エラーメッセージ")

    # ログファイルの内容を検証
    log_content = log_file.read_text(encoding="utf-8-sig")
    assert "情報メッセージ" in log_content
    assert "警告メッセージ" in log_content
    assert "エラーメッセージ" in log_content

    # エラーログの内容を検証
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
