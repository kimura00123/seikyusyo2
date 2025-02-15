"""
バリデーション機能のテスト
"""

import pytest
from datetime import datetime
from src.core.validation import (
    ValidationError,
    ValidationResult,
    ValidationRule,
    Validator,
)
from src.models.document import DocumentStructure, CustomerEntry, EntryDetail


def test_validation_error_model():
    """ValidationErrorモデルのテスト"""
    error = ValidationError(
        field="test_field",
        message="テストエラー",
        severity="error",
        value="invalid_value",
    )
    assert error.field == "test_field"
    assert error.message == "テストエラー"
    assert error.severity == "error"
    assert error.value == "invalid_value"


def test_validation_result_model():
    """ValidationResultモデルのテスト"""
    error = ValidationError(field="test", message="エラー", severity="error")
    warning = ValidationError(field="test", message="警告", severity="warning")
    result = ValidationResult(
        is_valid=False,
        errors=[error],
        warnings=[warning],
        normalized_data=None,
    )
    assert result.is_valid is False
    assert len(result.errors) == 1
    assert len(result.warnings) == 1
    assert result.normalized_data is None


class TestValidationRule:
    """ValidationRuleクラスのテスト"""

    def test_validate_customer_code(self):
        """顧客コードバリデーションのテスト"""
        rule = ValidationRule()

        # 正常系
        assert rule.validate_customer_code("ABC123") is None
        assert rule.validate_customer_code("ABCD1234") is None

        # 異常系
        assert rule.validate_customer_code("") is not None  # 空文字
        assert rule.validate_customer_code("abc") is not None  # 短すぎる
        assert rule.validate_customer_code("abc123") is not None  # 小文字
        assert rule.validate_customer_code("ABCD12345678") is not None  # 長すぎる
        assert rule.validate_customer_code("ABC-123") is not None  # 不正な文字

    def test_validate_amount(self):
        """金額バリデーションのテスト"""
        rule = ValidationRule()

        # 正常系
        assert rule.validate_amount("¥1,000") is None
        assert rule.validate_amount("1000") is None
        assert rule.validate_amount("¥999,999,999") is None

        # 異常系
        assert rule.validate_amount("") is not None  # 空文字
        assert rule.validate_amount("abc") is not None  # 数値以外
        assert rule.validate_amount("-1,000") is not None  # 負の値
        assert rule.validate_amount("¥1,000,000,000") is not None  # 上限超過

    def test_validate_tax_rate(self):
        """税率バリデーションのテスト"""
        rule = ValidationRule()

        # 正常系
        assert rule.validate_tax_rate("0%") is None
        assert rule.validate_tax_rate("8%") is None
        assert rule.validate_tax_rate("10%") is None

        # 異常系
        assert rule.validate_tax_rate("") is not None  # 空文字
        assert rule.validate_tax_rate("5%") is not None  # 不正な税率
        assert rule.validate_tax_rate("abc") is not None  # 数値以外
        assert rule.validate_tax_rate("abc") is not None  # 数値以外
        assert rule.validate_tax_rate("15%") is not None  # 不正な税率

    def test_validate_date_range(self):
        """日付範囲バリデーションのテスト"""
        rule = ValidationRule()

        # 正常系
        assert rule.validate_date_range("2024/01/01-2024/01/31") is None
        assert rule.validate_date_range(None) is None  # オプショナル

        # 異常系
        assert rule.validate_date_range("2024/01/01") is not None  # 不正な形式
        assert (
            rule.validate_date_range("2024/01/31-2024/01/01") is not None
        )  # 逆転した日付
        assert (
            rule.validate_date_range("2024-01-01-2024-01-31") is not None
        )  # 不正な区切り文字
        assert rule.validate_date_range("2024/13/01-2024/12/31") is not None  # 不正な月


class TestValidator:
    """Validatorクラスのテスト"""

    @pytest.fixture
    def valid_document(self) -> DocumentStructure:
        """正常なドキュメントデータを提供"""
        return DocumentStructure(
            pdf_filename="test.pdf",
            total_amount="¥10,000",
            customers=[
                CustomerEntry(
                    customer_code="ABC123",
                    customer_name="テスト顧客",
                    department="営業部",
                    box_number="BOX001",
                    entries=[
                        EntryDetail(
                            no="001",
                            description="テスト商品",
                            tax_rate="10%",
                            amount="¥1,000",
                            page_no=1,
                            date_range="2024/01/01-2024/01/31",
                        )
                    ],
                )
            ],
        )

    def test_validate_success(self, valid_document):
        """バリデーション成功のテスト"""
        validator = Validator()
        result = validator.validate(valid_document)
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.normalized_data is not None

    def test_validate_with_errors(self):
        """バリデーションエラーのテスト"""
        document = DocumentStructure(
            pdf_filename="test.pdf",
            total_amount="¥10,000",
            customers=[
                CustomerEntry(
                    customer_code="abc123",  # 小文字は不正
                    customer_name="テスト顧客",
                    department="営業部",
                    box_number="BOX001",
                    entries=[
                        EntryDetail(
                            no="001",
                            description="テスト商品",
                            tax_rate="5%",  # 不正な税率
                            amount="-1,000",  # 負の金額
                            page_no=1,
                            date_range="2024/01/31-2024/01/01",  # 不正な日付範囲
                        )
                    ],
                )
            ],
        )
        validator = Validator()
        result = validator.validate(document)
        assert not result.is_valid
        assert len(result.errors) == 3  # 顧客コード、税率、金額のエラー
        assert len(result.warnings) == 1  # 日付範囲の警告

    def test_validation_result_cache(self, valid_document):
        """バリデーション結果のキャッシュテスト"""
        validator = Validator()
        document_id = "test-doc-001"

        # 初回バリデーション
        validator.validate(valid_document, document_id=document_id)

        # キャッシュからの取得
        cached_result = validator.get_validation_result(document_id)
        assert cached_result is not None
        assert cached_result["is_valid"]
        assert len(cached_result["errors"]) == 0
        assert len(cached_result["warnings"]) == 0

        # 存在しないドキュメントID
        assert validator.get_validation_result("non-existent") is None

    def test_data_normalization(self, valid_document):
        """データ正規化のテスト"""
        validator = Validator()
        result = validator.validate(valid_document)
        normalized = result.normalized_data

        # 金額の正規化
        assert (
            normalized["customers"][0]["entries"][0]["amount"] == "1000"
        )  # カンマと円記号が除去される

        # 税率の正規化
        assert (
            normalized["customers"][0]["entries"][0]["tax_rate"] == "10"
        )  # %記号が除去される

        # 日付範囲の正規化
        assert (
            normalized["customers"][0]["entries"][0]["date_range"]
            == "2024/01/01-2024/01/31"
        )  # 形式が統一される
