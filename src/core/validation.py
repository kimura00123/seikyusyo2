from typing import Dict, Any, List
from pydantic import BaseModel


class ValidationError(BaseModel):
    field: str
    message: str
    severity: str = "error"


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationError]


class ValidationEngine:
    def __init__(self):
        self.rules = [
            self._validate_required_fields,
            self._validate_amounts,
            self._validate_tax_rates,
        ]

    def validate_invoice(self, document: Dict[str, Any]) -> ValidationResult:
        """請求書データのバリデーションを実行する"""
        errors = []

        for rule in self.rules:
            rule_errors = rule(document)
            errors.extend(rule_errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _validate_required_fields(
        self, document: Dict[str, Any]
    ) -> List[ValidationError]:
        """必須フィールドの検証"""
        errors = []

        # ドキュメントレベルの必須フィールド
        if not document.get("total_amount"):
            errors.append(
                ValidationError(field="total_amount", message="合計金額は必須です")
            )

        # 顧客情報の必須フィールド
        for customer in document.get("customers", []):
            if not customer.get("customer_code"):
                errors.append(
                    ValidationError(
                        field="customer_code", message="取引先コードは必須です"
                    )
                )
            if not customer.get("customer_name"):
                errors.append(
                    ValidationError(field="customer_name", message="取引先名は必須です")
                )

            # 明細行の必須フィールド
            for entry in customer.get("entries", []):
                if not entry.get("no"):
                    errors.append(
                        ValidationError(field="no", message="明細番号は必須です")
                    )
                if not entry.get("description"):
                    errors.append(
                        ValidationError(field="description", message="商品名は必須です")
                    )
                if not entry.get("amount"):
                    errors.append(
                        ValidationError(field="amount", message="金額は必須です")
                    )

        return errors

    def _validate_amounts(self, document: Dict[str, Any]) -> List[ValidationError]:
        """金額の整合性検証"""
        errors = []

        try:
            total_amount = int(document.get("total_amount", "0").replace(",", ""))
            sum_amount = 0

            for customer in document.get("customers", []):
                for entry in customer.get("entries", []):
                    try:
                        amount = int(entry.get("amount", "0").replace(",", ""))
                        sum_amount += amount
                    except ValueError:
                        errors.append(
                            ValidationError(
                                field="amount",
                                message=f"金額の形式が不正です: {entry.get('amount')}",
                                severity="error",
                            )
                        )

            if total_amount != sum_amount:
                errors.append(
                    ValidationError(
                        field="total_amount",
                        message=f"合計金額が一致しません（明細合計: {sum_amount:,}円, 合計金額: {total_amount:,}円）",
                        severity="warning",
                    )
                )

        except ValueError:
            errors.append(
                ValidationError(
                    field="total_amount",
                    message=f"合計金額の形式が不正です: {document.get('total_amount')}",
                    severity="error",
                )
            )

        return errors

    def _validate_tax_rates(self, document: Dict[str, Any]) -> List[ValidationError]:
        """税率の検証"""
        errors = []
        valid_rates = ["8%", "10%"]

        for customer in document.get("customers", []):
            for entry in customer.get("entries", []):
                tax_rate = entry.get("tax_rate")
                if tax_rate and tax_rate not in valid_rates:
                    errors.append(
                        ValidationError(
                            field="tax_rate",
                            message=f"不正な税率です: {tax_rate}（有効な税率: {', '.join(valid_rates)}）",
                            severity="warning",
                        )
                    )

        return errors
