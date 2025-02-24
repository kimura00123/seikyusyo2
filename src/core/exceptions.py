from typing import Optional, Dict, Any
from .errors import ErrorCode

class AppException(Exception):
    """アプリケーション例外の基底クラス"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(message or str(error_code))


class PDFProcessingError(AppException):
    """PDF処理関連のエラー"""
    pass


class StructuringError(AppException):
    """構造化処理関連のエラー"""
    pass


class ValidationError(AppException):
    """バリデーション関連のエラー"""
    pass


class ImageProcessingError(AppException):
    """画像処理関連のエラー"""
    pass


class DatabaseError(AppException):
    """データベース関連のエラー"""
    pass 