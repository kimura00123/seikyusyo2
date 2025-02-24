from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorLevel(str, Enum):
    """エラーレベルの定義"""
    FATAL = "fatal"      # システム停止を伴う重大なエラー
    ERROR = "error"      # 処理を継続できない重大なエラー
    WARNING = "warning"  # 処理は継続可能な警告
    INFO = "info"        # 情報提供


class ErrorCode(str, Enum):
    """エラーコードの定義"""
    # システムエラー (1000番台)
    SYSTEM_ERROR = "E1001"
    UNEXPECTED_ERROR = "E1002"
    INITIALIZATION_ERROR = "E1003"
    
    # PDF処理エラー (2000番台)
    PDF_PARSE_ERROR = "E2001"
    PDF_VERSION_ERROR = "E2002"
    PDF_ENCRYPTION_ERROR = "E2003"
    PDF_FILE_ERROR = "E2004"
    
    # 構造化エラー (3000番台)
    STRUCTURING_ERROR = "E3001"
    API_ERROR = "E3002"
    INVALID_FORMAT = "E3003"
    
    # バリデーションエラー (4000番台)
    VALIDATION_ERROR = "E4001"
    REQUIRED_FIELD_MISSING = "E4002"
    INVALID_VALUE = "E4003"
    
    # 画像処理エラー (5000番台)
    IMAGE_PROCESSING_ERROR = "E5001"
    IMAGE_EXTRACTION_ERROR = "E5002"
    
    # データベースエラー (6000番台)
    DB_CONNECTION_ERROR = "E6001"
    DB_OPERATION_ERROR = "E6002"


class AppError(BaseModel):
    """アプリケーションエラーモデル"""
    code: ErrorCode
    level: ErrorLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None

    class Config:
        use_enum_values = True


class ErrorDefinition:
    """エラー定義"""
    DEFINITIONS = {
        # システムエラー (1000番台)
        ErrorCode.SYSTEM_ERROR: {
            "level": ErrorLevel.FATAL,
            "message": "システムエラーが発生しました",
            "suggestion": "システム管理者に連絡してください"
        },
        ErrorCode.UNEXPECTED_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "予期せぬエラーが発生しました",
            "suggestion": "システム管理者に連絡してください"
        },
        ErrorCode.INITIALIZATION_ERROR: {
            "level": ErrorLevel.FATAL,
            "message": "システムの初期化に失敗しました",
            "suggestion": "ログを確認し、必要な環境が整っているか確認してください"
        },

        # PDF処理エラー (2000番台)
        ErrorCode.PDF_PARSE_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "PDFの解析に失敗しました",
            "suggestion": "PDFファイルが破損していないか確認してください"
        },
        ErrorCode.PDF_VERSION_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "サポートされていないPDFバージョンです",
            "suggestion": "PDF 1.4以上のバージョンで保存し直してください"
        },
        ErrorCode.PDF_ENCRYPTION_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "暗号化されたPDFは処理できません",
            "suggestion": "暗号化を解除してから再度アップロードしてください"
        },
        ErrorCode.PDF_FILE_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "PDFファイルの読み込みに失敗しました",
            "suggestion": "ファイルが正しくアップロードされているか確認してください"
        },

        # 構造化エラー (3000番台)
        ErrorCode.STRUCTURING_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "請求書の構造化に失敗しました",
            "suggestion": "請求書のフォーマットを確認してください"
        },
        ErrorCode.API_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "API呼び出しでエラーが発生しました",
            "suggestion": "しばらく待ってから再試行してください"
        },
        ErrorCode.INVALID_FORMAT: {
            "level": ErrorLevel.ERROR,
            "message": "無効なデータ形式です",
            "suggestion": "入力データの形式を確認してください"
        },

        # バリデーションエラー (4000番台)
        ErrorCode.VALIDATION_ERROR: {
            "level": ErrorLevel.WARNING,
            "message": "入力値の検証に失敗しました",
            "suggestion": "入力内容を確認してください"
        },
        ErrorCode.REQUIRED_FIELD_MISSING: {
            "level": ErrorLevel.WARNING,
            "message": "必須項目が不足しています",
            "suggestion": "必須項目を確認して再度入力してください"
        },
        ErrorCode.INVALID_VALUE: {
            "level": ErrorLevel.WARNING,
            "message": "入力値が無効です",
            "suggestion": "正しい形式で入力してください"
        },

        # 画像処理エラー (5000番台)
        ErrorCode.IMAGE_PROCESSING_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "画像処理に失敗しました",
            "suggestion": "画像の品質を確認してください"
        },
        ErrorCode.IMAGE_EXTRACTION_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "画像の抽出に失敗しました",
            "suggestion": "PDFの品質を確認してください"
        },

        # データベースエラー (6000番台)
        ErrorCode.DB_CONNECTION_ERROR: {
            "level": ErrorLevel.FATAL,
            "message": "データベース接続エラー",
            "suggestion": "ネットワーク接続を確認してください"
        },
        ErrorCode.DB_OPERATION_ERROR: {
            "level": ErrorLevel.ERROR,
            "message": "データベース操作エラー",
            "suggestion": "データの整合性を確認してください"
        }
    }

    @classmethod
    def get_definition(cls, code: ErrorCode) -> Dict[str, Any]:
        """エラー定義の取得"""
        return cls.DEFINITIONS.get(code, {
            "level": ErrorLevel.ERROR,
            "message": "未定義のエラーが発生しました",
            "suggestion": "システム管理者に連絡してください"
        }) 