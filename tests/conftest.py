"""
共有テストフィクスチャの定義

このモジュールでは、複数のテストで共有されるフィクスチャを定義します。
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from src.api.main import app
from src.utils.config import Settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """テスト用の設定を提供"""
    return Settings(
        AZURE_OPENAI_API_KEY="test-key",
        AZURE_OPENAI_ENDPOINT="https://test-endpoint",
        AZURE_OPENAI_API_VERSION="2024-02-14",
        COSMOS_DB_CONNECTION_STRING="test-connection-string",
        COSMOS_DB_DATABASE_NAME="test-db",
        COSMOS_DB_CONTAINER_NAME="test-container",
    )


@pytest.fixture(scope="session")
def test_client(test_settings: Settings) -> TestClient:
    """テスト用のFastAPIクライアント"""
    return TestClient(app)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """テスト用の一時ディレクトリを提供"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_pdf(temp_dir: Path) -> Path:
    """テスト用のサンプルPDFファイルを提供"""
    pdf_path = temp_dir / "sample.pdf"
    # TODO: サンプルPDFファイルの作成ロジックを実装
    return pdf_path


@pytest.fixture
def mock_cosmos_client(mocker: MockerFixture) -> Dict[str, Any]:
    """CosmosDBクライアントのモックを提供"""
    mock_client = mocker.MagicMock()
    mock_container = mocker.MagicMock()
    mock_client.get_database_client.return_value.get_container_client.return_value = (
        mock_container
    )

    return {"client": mock_client, "container": mock_container}


@pytest.fixture
def mock_openai_client(mocker: MockerFixture) -> MockerFixture:
    """Azure OpenAI APIクライアントのモックを提供"""
    mock_client = mocker.MagicMock()
    mock_client.chat.completions.create.return_value = mocker.MagicMock(
        choices=[
            mocker.MagicMock(message=mocker.MagicMock(content='{"test": "response"}'))
        ]
    )
    return mock_client


def pytest_configure(config):
    """テスト設定の初期化"""
    # カスタムマーカーの登録
    config.addinivalue_line(
        "markers", "integration: integration tests that require external services"
    )
    config.addinivalue_line(
        "markers", "e2e: end-to-end tests that require the full system"
    )


def pytest_collection_modifyitems(config, items):
    """テストの収集時の処理"""
    # 統合テストとE2Eテストにマーカーを追加
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
