import traceback
from typing import Any, Dict, Optional, Type

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .errors import AppError, ErrorCode, ErrorDefinition, ErrorLevel
from .exceptions import (
    AppException,
    PDFProcessingError,
    StructuringError,
    ValidationError as AppValidationError,
    ImageProcessingError,
    DatabaseError
)
from src.utils.logger import get_logger
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI

logger = get_logger()


class ErrorHandler:
    """エラーハンドラークラス"""

    ERROR_MAPPINGS = {
        PDFProcessingError: {
            "default_code": ErrorCode.PDF_PARSE_ERROR,
            "status_code": status.HTTP_400_BAD_REQUEST
        },
        StructuringError: {
            "default_code": ErrorCode.STRUCTURING_ERROR,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        },
        AppValidationError: {
            "default_code": ErrorCode.VALIDATION_ERROR,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY
        },
        ImageProcessingError: {
            "default_code": ErrorCode.IMAGE_PROCESSING_ERROR,
            "status_code": status.HTTP_400_BAD_REQUEST
        },
        DatabaseError: {
            "default_code": ErrorCode.DB_CONNECTION_ERROR,
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE
        }
    }

    def __init__(self):
        self.logger = get_logger()

    async def handle_error(
        self,
        request: Request,
        exc: Exception,
        error_code: Optional[ErrorCode] = None,
        status_code: Optional[int] = None,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """エラーのハンドリング"""
        # カスタム例外の場合はマッピングを使用
        if isinstance(exc, AppException):
            error_code = exc.error_code or self._get_default_error_code(exc)
            status_code = status_code or self._get_default_status_code(exc)
            additional_info = exc.details or additional_info

        # デフォルトのエラーコードと状態コード
        error_code = error_code or ErrorCode.UNEXPECTED_ERROR
        status_code = status_code or status.HTTP_500_INTERNAL_SERVER_ERROR

        # エラー定義の取得
        error_def = ErrorDefinition.get_definition(error_code)
        
        # エラー情報の構築
        error = AppError(
            code=error_code,
            level=error_def["level"],
            message=getattr(exc, 'message', error_def["message"]),
            details={
                "path": str(request.url),
                "method": request.method,
                "error_type": exc.__class__.__name__,
                "error_detail": str(exc),
                **(additional_info or {})
            },
            suggestion=error_def["suggestion"]
        )

        # エラーレベルに応じたログ出力
        self._log_error(error, exc)

        # レスポンスの構築
        return JSONResponse(
            status_code=status_code,
            content=error.dict()
        )

    def _get_default_error_code(self, exc: AppException) -> ErrorCode:
        """例外クラスに対応するデフォルトのエラーコードを取得"""
        mapping = self.ERROR_MAPPINGS.get(exc.__class__, {})
        return mapping.get("default_code", ErrorCode.UNEXPECTED_ERROR)

    def _get_default_status_code(self, exc: AppException) -> int:
        """例外クラスに対応するデフォルトのステータスコードを取得"""
        mapping = self.ERROR_MAPPINGS.get(exc.__class__, {})
        return mapping.get("status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _log_error(self, error: AppError, exc: Exception) -> None:
        """エラーログの出力"""
        log_message = f"{error.code}: {error.message}"
        
        if error.level == ErrorLevel.FATAL:
            self.logger.critical(log_message, exc_info=exc)
        elif error.level == ErrorLevel.ERROR:
            self.logger.error(log_message, exc_info=exc)
        elif error.level == ErrorLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """エラーハンドリングミドルウェア"""

    def __init__(self, app: FastAPI = None):
        if app:
            super().__init__(app)
        self.error_handler = ErrorHandler()

    async def dispatch(self, request: Request, call_next):
        """リクエスト処理中の例外をキャッチする"""
        try:
            return await call_next(request)
        except ValidationError as exc:
            return await self.handle_validation_error(request, exc)
        except Exception as exc:
            return await self.handle_unexpected_error(request, exc)

    async def handle_validation_error(
        self,
        request: Request,
        exc: ValidationError
    ) -> JSONResponse:
        """バリデーションエラーのハンドリング"""
        return await self.error_handler.handle_error(
            request=request,
            exc=exc,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            additional_info={"validation_errors": exc.errors()}
        )

    async def handle_unexpected_error(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """予期せぬエラーのハンドリング"""
        return await self.error_handler.handle_error(
            request=request,
            exc=exc,
            error_code=ErrorCode.UNEXPECTED_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 