import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .structuring import DocumentStructure
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(BaseModel):
    """バリデーションエラー情報"""

    field: str = Field(..., description="エラーが発生したフィールド")
    message: str = Field(..., description="エラーメッセージ")
    severity: str = Field("error", description="エラーの重要度")
    value: Any = Field(None, description="エラーの対象値")


class ValidationResult(BaseModel):
    """バリデーション結果"""

    is_valid: bool = Field(False, description="バリデーション結果")
    errors: List[ValidationError] = Field(
        default_factory=list, description="エラーリスト"
    )
    warnings: List[ValidationError] = Field(
        default_factory=list, description="警告リスト"
    )
    normalized_data: Optional[Dict] = Field(None, description="正規化されたデータ")


class ValidationRule:
    """バリデーションルール"""

    @staticmethod
    def validate_customer_code(code: str) -> Optional[str]:
        """
        顧客コードを検証する

        Args:
            code (str): 顧客コード

        Returns:
            Optional[str]: エラーメッセージ。問題なければNone
        """
        if not code:
            return "顧客コードは必須です"
        if not re.match(r"^[A-Z0-9]{4,10}$", code):
            return "顧客コードは4-10文字の英数字である必要があります"
        return None

    @staticmethod
    def validate_amount(amount: str) -> Optional[str]:
        """
        金額を検証する

        Args:
            amount (str): 金額

        Returns:
            Optional[str]: エラーメッセージ。問題なければNone
        """
        if not amount:
            return "金額は必須です"
        try:
            # カンマと円記号を除去して数値変換
            value = int(amount.replace(",", "").replace("¥", ""))
            if value < 0:
                return "金額は0以上である必要があります"
            if value > 999999999:
                return "金額が上限を超えています"
        except ValueError:
            return "金額の形式が不正です"
        return None

    @staticmethod
    def validate_tax_rate(rate: str) -> Optional[str]:
        """
        税率を検証する

        Args:
            rate (str): 税率

        Returns:
            Optional[str]: エラーメッセージ。問題なければNone
        """
        if not rate:
            return "税率は必須です"
        try:
            # %記号を除去して数値変換
            value = float(rate.replace("%", ""))
            if value not in [0, 8, 10]:
                return "税率は0%, 8%, 10%のいずれかである必要があります"
        except ValueError:
            return "税率の形式が不正です"
        return None

    @staticmethod
    def validate_date_range(date_range: Optional[str]) -> Optional[str]:
        """
        日付範囲を検証する

        Args:
            date_range (Optional[str]): 日付範囲

        Returns:
            Optional[str]: エラーメッセージ。問題なければNone
        """
        if not date_range:
            return None  # 日付範囲は任意

        # YYYY/MM/DD-YYYY/MM/DD 形式を期待
        pattern = r"^\d{4}/\d{2}/\d{2}-\d{4}/\d{2}/\d{2}$"
        if not re.match(pattern, date_range):
            return "日付範囲の形式が不正です（YYYY/MM/DD-YYYY/MM/DD）"

        try:
            start_date, end_date = date_range.split("-")
            start = datetime.strptime(start_date, "%Y/%m/%d")
            end = datetime.strptime(end_date, "%Y/%m/%d")
            if end < start:
                return "終了日は開始日以降である必要があります"
        except ValueError:
            return "日付の形式が不正です"

        return None


class Validator:
    """バリデーションエンジン"""

    def __init__(self):
        self.rules = ValidationRule()
        self._validation_cache = (
            {}
        )  # ドキュメントIDごとのバリデーション結果をキャッシュ

    def validate(
        self, data: DocumentStructure, document_id: Optional[str] = None
    ) -> ValidationResult:
        """
        データを検証する

        Args:
            data (DocumentStructure): 検証対象のデータ

        Returns:
            ValidationResult: 検証結果
        """
        try:
            errors = []
            warnings = []

            # 顧客情報の検証
            for customer in data.customers:
                # 顧客コードの検証
                if error := self.rules.validate_customer_code(customer.customer_code):
                    errors.append(
                        ValidationError(
                            field=f"customer_code",
                            message=error,
                            value=customer.customer_code,
                        )
                    )

                # 明細行の検証
                for entry in customer.entries:
                    # 金額の検証
                    if error := self.rules.validate_amount(entry.amount):
                        errors.append(
                            ValidationError(
                                field=f"amount", message=error, value=entry.amount
                            )
                        )

                    # 税率の検証
                    if error := self.rules.validate_tax_rate(entry.tax_rate):
                        errors.append(
                            ValidationError(
                                field=f"tax_rate", message=error, value=entry.tax_rate
                            )
                        )

                    # 日付範囲の検証
                    if error := self.rules.validate_date_range(entry.date_range):
                        warnings.append(
                            ValidationError(
                                field=f"date_range",
                                message=error,
                                severity="warning",
                                value=entry.date_range,
                            )
                        )

            # 正規化データの作成
            normalized_data = self._normalize_data(data)

            # 結果の作成
            result = ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                normalized_data=(
                    normalized_data.model_dump() if normalized_data else None
                ),
            )

            # ログ出力
            if result.is_valid:
                logger.info("バリデーション成功")
            else:
                logger.warning(
                    f"バリデーションエラー: {len(errors)}件のエラー, {len(warnings)}件の警告"
                )

            # バリデーション結果をキャッシュ
            if document_id:
                self._validation_cache[document_id] = result
                logger.info(f"バリデーション結果をキャッシュ: {document_id}")

            return result

        except Exception as e:
            logger.error(f"バリデーションでエラー: {e}", exc_info=True)
            raise

    def get_validation_result(self, document_id: str) -> Optional[Dict]:
        """
        キャッシュされたバリデーション結果を取得する

        Args:
            document_id (str): ドキュメントID

        Returns:
            Optional[Dict]: バリデーション結果。存在しない場合はNone
        """
        try:
            if document_id in self._validation_cache:
                result = self._validation_cache[document_id]
                return {
                    "is_valid": result.is_valid,
                    "errors": [
                        {"field": e.field, "message": e.message} for e in result.errors
                    ],
                    "warnings": [
                        {"field": w.field, "message": w.message}
                        for w in result.warnings
                    ],
                }
            return None

        except Exception as e:
            logger.error(f"バリデーション結果の取得でエラー: {e}", exc_info=True)
            raise

    def _normalize_data(self, data: DocumentStructure) -> DocumentStructure:
        """
        データを正規化する

        Args:
            data (DocumentStructure): 正規化対象のデータ

        Returns:
            DocumentStructure: 正規化されたデータ
        """
        try:
            # 新しいインスタンスを作成して変更を適用
            normalized = data.copy(deep=True)

            for customer in normalized.customers:
                for entry in customer.entries:
                    # 金額の正規化（カンマと円記号を除去）
                    entry.amount = entry.amount.replace(",", "").replace("¥", "")

                    # 税率の正規化（%記号を除去）
                    entry.tax_rate = entry.tax_rate.replace("%", "")

                    # 日付範囲の正規化（形式の統一）
                    if entry.date_range:
                        try:
                            start, end = entry.date_range.split("-")
                            start_date = datetime.strptime(start, "%Y/%m/%d")
                            end_date = datetime.strptime(end, "%Y/%m/%d")
                            entry.date_range = (
                                f"{start_date.strftime('%Y/%m/%d')}-"
                                f"{end_date.strftime('%Y/%m/%d')}"
                            )
                        except ValueError:
                            # 日付の解析に失敗した場合は元の値を維持
                            pass

            return normalized

        except Exception as e:
            logger.error(f"データの正規化でエラー: {e}", exc_info=True)
            raise


# 使用例:
"""
validator = Validator()

# バリデーション実行
result = validator.validate(document_data)

if result.is_valid:
    # 正規化されたデータを使用
    normalized_data = result.normalized_data
else:
    # エラーを処理
    for error in result.errors:
        print(f"エラー: {error.field} - {error.message}")
    for warning in result.warnings:
        print(f"警告: {warning.field} - {warning.message}")
"""
