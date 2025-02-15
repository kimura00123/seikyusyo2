"""
ドキュメント処理APIのテスト
"""

import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import UploadFile

from src.api.main import app
from src.api.routers.document import (
    ValidationError,
    ValidationWarning,
    ValidationResponse,
    ProcessingStatus,
)


def test_validation_error_model():
    """ValidationErrorモデルのテスト"""
    error = ValidationError(field="test_field", message="テストエラー")
    assert error.field == "test_field"
    assert error.message == "テストエラー"


def test_validation_warning_model():
    """ValidationWarningモデルのテスト"""
    warning = ValidationWarning(field="test_field", message="テスト警告")
    assert warning.field == "test_field"
    assert warning.message == "テスト警告"


def test_validation_response_model():
    """ValidationResponseモデルのテスト"""
    response = ValidationResponse(
        is_valid=False,
        errors=[ValidationError(field="field1", message="エラー1")],
        warnings=[ValidationWarning(field="field2", message="警告1")],
    )
    assert response.is_valid is False
    assert len(response.errors) == 1
    assert len(response.warnings) == 1
    assert response.errors[0].field == "field1"
    assert response.warnings[0].field == "field2"


def test_processing_status_model():
    """ProcessingStatusモデルのテスト"""
    status = ProcessingStatus(
        status="processing",
        progress=50,
        message="処理中",
        errors=["エラー1"],
    )
    assert status.status == "processing"
    assert status.progress == 50
    assert status.message == "処理中"
    assert len(status.errors) == 1


class TestDocumentAPI:
    """ドキュメント処理APIのテスト"""

    @pytest.fixture
    def client(self):
        """テストクライアントを提供"""
        return TestClient(app)

    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """テスト用のPDFファイルを提供"""
        pdf_path = tmp_path / "test.pdf"
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\ntest content")
        return pdf_path

    @pytest.fixture
    def mock_temp_dir(self, tmp_path):
        """一時ディレクトリのモックを提供"""
        temp_dir = tmp_path / "temp"
        temp_dir.mkdir()
        (temp_dir / "uploads").mkdir()
        (temp_dir / "images").mkdir()
        (temp_dir / "processed").mkdir()
        return temp_dir

    def test_upload_document_success(self, client, sample_pdf, mock_temp_dir, mocker):
        """ドキュメントアップロードの成功テスト"""
        # モックの設定
        mocker.patch(
            "src.api.routers.document.Config.get_temp_dir",
            return_value=mock_temp_dir,
        )
        mocker.patch(
            "src.api.routers.document.PDFParser.extract_text_with_positions",
            return_value={1: []},
        )
        mocker.patch(
            "src.api.routers.document.StructuringEngine.structure_invoice",
            return_value=MagicMock(),
        )
        mocker.patch(
            "src.api.routers.document.Validator.validate",
            return_value=MagicMock(is_valid=True, errors=[], warnings=[]),
        )
        mocker.patch(
            "src.api.routers.document.ImageProcessor.extract_detail_regions",
            return_value=[],
        )
        mocker.patch(
            "src.api.routers.document.ImageProcessor.extract_detail_images",
            return_value=[],
        )
        mocker.patch(
            "src.api.routers.document.ExcelExporter.export_to_excel",
            return_value=str(mock_temp_dir / "processed" / "test.xlsx"),
        )

        # リクエストの実行
        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/document/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

        # レスポンスの検証
        assert response.status_code == 202
        assert response.json()["status"] == "success"
        assert "document_id" in response.json()
        assert "data" in response.json()

    def test_upload_document_invalid_file(self, client):
        """不正なファイルのアップロードテスト"""
        response = client.post(
            "/document/upload",
            files={"file": ("test.txt", b"test", "text/plain")},
        )
        assert response.status_code == 400
        assert "PDFファイルのみ" in response.json()["detail"]

    def test_get_processing_status(self, client):
        """処理状態取得のテスト"""
        # 処理状態の設定
        document_id = "test_doc"
        app.state.processing_status = {
            document_id: {
                "status": "processing",
                "progress": 50,
                "message": "処理中",
                "errors": [],
            }
        }

        # リクエストの実行
        response = client.get(f"/document/status/{document_id}")

        # レスポンスの検証
        assert response.status_code == 200
        assert response.json()["status"] == "processing"
        assert response.json()["progress"] == 50

        # 存在しないドキュメントID
        response = client.get("/document/status/nonexistent")
        assert response.status_code == 404

    def test_get_validation_result(self, client, mocker):
        """バリデーション結果取得のテスト"""
        # モックの設定
        document_id = "test_doc"
        mock_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }
        mocker.patch(
            "src.api.routers.document.Validator.get_validation_result",
            return_value=mock_result,
        )

        # リクエストの実行
        response = client.get(f"/document/validation/{document_id}")

        # レスポンスの検証
        assert response.status_code == 200
        assert response.json()["is_valid"] is True

        # 存在しないバリデーション結果
        mocker.patch(
            "src.api.routers.document.Validator.get_validation_result",
            return_value=None,
        )
        response = client.get(f"/document/validation/{document_id}")
        assert response.status_code == 404

    def test_get_detail_images(self, client, mock_temp_dir, mocker):
        """明細画像取得のテスト"""
        # モックの設定
        document_id = "test_doc"
        image_dir = mock_temp_dir / "images" / document_id
        image_dir.mkdir(parents=True)
        (image_dir / "page1_detail1.jpg").touch()
        (image_dir / "page1_detail2.jpg").touch()
        (image_dir / "page2_detail1.jpg").touch()

        mocker.patch(
            "src.api.routers.document.Config.get_temp_dir",
            return_value=mock_temp_dir,
        )

        # リクエストの実行（全ページ）
        response = client.get(f"/document/images/{document_id}")
        assert response.status_code == 200
        assert len(response.json()) == 3

        # リクエストの実行（ページ指定）
        response = client.get(f"/document/images/{document_id}?page=1")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # 存在しないドキュメントID
        response = client.get("/document/images/nonexistent")
        assert response.status_code == 404

    def test_download_file(self, client, mock_temp_dir, mocker):
        """ファイルダウンロードのテスト"""
        # モックの設定
        document_id = "test_doc"
        excel_path = mock_temp_dir / "processed" / f"{document_id}.xlsx"
        excel_path.parent.mkdir(parents=True, exist_ok=True)
        excel_path.touch()

        mocker.patch(
            "src.api.routers.document.Config.get_temp_dir",
            return_value=mock_temp_dir,
        )

        # リクエストの実行
        response = client.get(f"/document/download/{document_id}")
        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 存在しないファイル
        response = client.get("/document/download/nonexistent")
        assert response.status_code == 404

    def test_cleanup_temp_files(self, client, mock_temp_dir, mocker):
        """一時ファイルのクリーンアップテスト"""
        # モックの設定
        mocker.patch(
            "src.api.routers.document.Config.get_temp_dir",
            return_value=mock_temp_dir,
        )
        mocker.patch(
            "src.api.routers.document.TempFileManager.cleanup_old_files",
            return_value=5,
        )

        # リクエストの実行
        response = client.post("/document/cleanup?max_age=24")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "5件" in response.json()["message"]
