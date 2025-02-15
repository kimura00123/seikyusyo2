"""
環境設定のテスト
"""

import os
import pytest
from pathlib import Path
from src.utils.config import Config


@pytest.fixture
def mock_env(monkeypatch):
    """環境変数のモックを提供"""
    # 既存の環境変数をクリア
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("IMAGE_DPI", raising=False)
    monkeypatch.delenv("IMAGE_QUALITY", raising=False)
    monkeypatch.delenv("TEMP_DIR", raising=False)


def test_default_values(mock_env):
    """デフォルト値のテスト"""
    assert Config.ENV == "development"
    assert Config.LOG_LEVEL == "INFO"
    assert Config.PORT == 8000
    assert Config.IMAGE_DPI == 200
    assert Config.IMAGE_QUALITY == 95
    assert isinstance(Config.get_temp_dir(), Path)


def test_environment_variables(monkeypatch):
    """環境変数からの値読み込みテスト"""
    # 環境変数の設定
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("IMAGE_DPI", "300")
    monkeypatch.setenv("IMAGE_QUALITY", "90")
    monkeypatch.setenv("TEMP_DIR", "/custom/temp")

    # 設定値の検証
    assert Config.ENV == "production"
    assert Config.LOG_LEVEL == "DEBUG"
    assert Config.PORT == 9000
    assert Config.IMAGE_DPI == 300
    assert Config.IMAGE_QUALITY == 90
    assert str(Config.get_temp_dir()) == "/custom/temp"


def test_environment_detection(monkeypatch):
    """環境判定のテスト"""
    # 開発環境
    monkeypatch.setenv("ENV", "development")
    assert Config.is_development() is True
    assert Config.is_production() is False

    # 本番環境
    monkeypatch.setenv("ENV", "production")
    assert Config.is_development() is False
    assert Config.is_production() is True

    # その他の環境
    monkeypatch.setenv("ENV", "staging")
    assert Config.is_development() is False
    assert Config.is_production() is False


def test_get_method():
    """getメソッドのテスト"""
    # 存在する環境変数
    os.environ["TEST_VAR"] = "test_value"
    assert Config.get("TEST_VAR") == "test_value"

    # 存在しない環境変数
    assert Config.get("NONEXISTENT_VAR") is None
    assert Config.get("NONEXISTENT_VAR", "default") == "default"


def test_get_temp_dir(monkeypatch):
    """一時ディレクトリ取得のテスト"""
    # デフォルトの一時ディレクトリ
    temp_dir = Config.get_temp_dir()
    assert isinstance(temp_dir, Path)
    assert str(temp_dir).endswith("temp")

    # カスタムの一時ディレクトリ
    monkeypatch.setenv("TEMP_DIR", "/custom/temp")
    assert str(Config.get_temp_dir()) == "/custom/temp"


def test_validation_development(mock_env):
    """開発環境でのバリデーションテスト"""
    # 開発環境では必須項目が少ない
    monkeypatch = mock_env
    monkeypatch.setenv("ENV", "development")
    assert Config.validate() is True


def test_validation_production(mock_env):
    """本番環境でのバリデーションテスト"""
    monkeypatch = mock_env
    monkeypatch.setenv("ENV", "production")

    # 必須項目が不足している場合
    with pytest.raises(ValueError) as exc_info:
        Config.validate()
    assert "必須の環境変数が設定されていません" in str(exc_info.value)
    assert "AZURE_OPENAI_API_KEY" in str(exc_info.value)

    # 必須項目がすべて設定されている場合
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "test-endpoint")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "test-deployment")
    assert Config.validate() is True


def test_base_dir():
    """BASE_DIRの設定テスト"""
    assert isinstance(Config.BASE_DIR, Path)
    assert Config.BASE_DIR.exists()
    assert (Config.BASE_DIR / "src").exists()
