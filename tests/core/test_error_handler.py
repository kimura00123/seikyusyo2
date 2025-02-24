import pytest
from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.core.error_handler import ErrorHandler
from src.core.errors import ErrorCode, ErrorLevel
from src.core.exceptions import (
    PDFProcessingError,
    StructuringError,
    ValidationError,
    ImageProcessingError,
    DatabaseError
)


@pytest.fixture
def error_handler():
    return ErrorHandler()


@pytest.fixture
def mock_request():
    return Request(scope={
        'type': 'http',
        'method': 'POST',
        'path': '/test',
        'headers': []
    })


@pytest.mark.asyncio
async def test_handle_pdf_processing_error(error_handler, mock_request):
    # PDFProcessingErrorのテスト
    exc = PDFProcessingError(
        error_code=ErrorCode.PDF_VERSION_ERROR,
        message="PDFバージョンが古すぎます",
        details={"version": "1.3"}
    )
    
    response = await error_handler.handle_error(mock_request, exc)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    content = response.body.decode()
    assert ErrorCode.PDF_VERSION_ERROR.value in content
    assert "PDFバージョンが古すぎます" in content
    assert '"version": "1.3"' in content


@pytest.mark.asyncio
async def test_handle_validation_error(error_handler, mock_request):
    # ValidationErrorのテスト
    exc = ValidationError(
        error_code=ErrorCode.REQUIRED_FIELD_MISSING,
        message="必須フィールドがありません",
        details={"field": "invoice_number"}
    )
    
    response = await error_handler.handle_error(mock_request, exc)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    content = response.body.decode()
    assert ErrorCode.REQUIRED_FIELD_MISSING.value in content
    assert "必須フィールドがありません" in content
    assert '"field": "invoice_number"' in content


@pytest.mark.asyncio
async def test_handle_unexpected_error(error_handler, mock_request):
    # 予期せぬエラーのテスト
    exc = Exception("予期せぬエラーが発生しました")
    
    response = await error_handler.handle_error(mock_request, exc)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    content = response.body.decode()
    assert ErrorCode.UNEXPECTED_ERROR.value in content


@pytest.mark.asyncio
async def test_handle_database_error(error_handler, mock_request):
    # DatabaseErrorのテスト
    exc = DatabaseError(
        error_code=ErrorCode.DB_CONNECTION_ERROR,
        message="データベースに接続できません",
        details={"host": "localhost"}
    )
    
    response = await error_handler.handle_error(mock_request, exc)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    content = response.body.decode()
    assert ErrorCode.DB_CONNECTION_ERROR.value in content
    assert "データベースに接続できません" in content


@pytest.mark.asyncio
async def test_error_levels(error_handler, mock_request):
    # 各エラーレベルのテスト
    test_cases = [
        (ErrorCode.SYSTEM_ERROR, ErrorLevel.FATAL),
        (ErrorCode.PDF_PARSE_ERROR, ErrorLevel.ERROR),
        (ErrorCode.REQUIRED_FIELD_MISSING, ErrorLevel.WARNING),
    ]
    
    for error_code, expected_level in test_cases:
        exc = Exception("テストエラー")
        response = await error_handler.handle_error(
            mock_request, exc, error_code=error_code
        )
        
        content = response.body.decode()
        assert f'"level": "{expected_level}"' in content 