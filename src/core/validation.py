from typing import Dict, Any, List
from pydantic import BaseModel
import logging
import re


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
            self._validate_sequential_numbers,
            self._validate_customer_code_diversity,
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

    def _validate_sequential_numbers(self, document: Dict[str, Any]) -> List[ValidationError]:
        """明細番号の連番チェック"""
        errors = []
        logger = logging.getLogger(__name__)
        
        # すべての明細番号を収集
        all_detail_numbers = []
        for customer in document.get("customers", []):
            for entry in customer.get("entries", []):
                detail_no = entry.get("no")
                if detail_no:
                    all_detail_numbers.append(detail_no)
        
        # 明細番号が存在しない場合はチェックしない
        if not all_detail_numbers:
            return errors
            
        # 明細番号から数値部分を抽出
        number_pattern = re.compile(r'(\d+)')
        numeric_details = []
        
        for detail_no in all_detail_numbers:
            match = number_pattern.search(str(detail_no))
            if match:
                numeric_details.append(int(match.group(1)))
        
        # 数値が抽出できない場合はチェックしない
        if not numeric_details:
            return errors
            
        # 数値をソート
        numeric_details.sort()
        
        # 最小値と最大値を取得
        min_no = numeric_details[0]
        max_no = numeric_details[-1]
        
        # 連番であるべき数値の範囲を生成
        expected_range = set(range(min_no, max_no + 1))
        actual_set = set(numeric_details)
        
        # 欠番を検出
        missing_numbers = expected_range - actual_set
        
        if missing_numbers:
            missing_str = ", ".join(str(num) for num in sorted(missing_numbers))
            logger.warning(f"明細番号に欠番があります: {missing_str}")
            errors.append(
                ValidationError(
                    field="detail_numbers",
                    message=f"明細番号に欠番があります: {missing_str}",
                    severity="warning"
                )
            )
            
        # 重複をチェック
        duplicates = []
        seen = set()
        
        for num in numeric_details:
            if num in seen:
                duplicates.append(num)
            else:
                seen.add(num)
                
        if duplicates:
            duplicate_str = ", ".join(str(num) for num in sorted(set(duplicates)))
            logger.warning(f"明細番号に重複があります: {duplicate_str}")
            errors.append(
                ValidationError(
                    field="detail_numbers",
                    message=f"明細番号に重複があります: {duplicate_str}",
                    severity="warning"
                )
            )
            
        return errors

    def _validate_amounts(self, document: Dict[str, Any]) -> List[ValidationError]:
        """金額の整合性検証"""
        errors = []
        
        # ロガーを取得
        logger = logging.getLogger(__name__)

        try:
            # 合計金額を文字列に変換してからreplace処理
            total_amount_str = str(document.get("total_amount", "0"))
            total_amount = int(total_amount_str.replace(",", ""))
            sum_amount = 0
            
            # 税率ごとの合計金額を計算するための辞書
            tax_totals = {
                "8%": 0,
                "10%": 0,
                "unknown": 0  # 税率が不明な場合
            }

            for customer in document.get("customers", []):
                for entry in customer.get("entries", []):
                    try:
                        # 明細金額を文字列に変換してからreplace処理
                        amount_str = str(entry.get("amount", "0"))
                        amount = int(amount_str.replace(",", ""))
                        
                        # 税率を取得（文字列に変換）
                        tax_rate = entry.get("tax_rate")
                        if tax_rate is not None:
                            tax_rate = str(tax_rate)
                        
                        # 税率ごとに金額を集計
                        if tax_rate == "8%":
                            tax_totals["8%"] += amount
                        elif tax_rate == "10%":
                            tax_totals["10%"] += amount
                        else:
                            # デフォルトは10%と仮定
                            tax_totals["unknown"] += amount
                            
                        sum_amount += amount
                    except ValueError:
                        errors.append(
                            ValidationError(
                                field="amount",
                                message=f"金額の形式が不正です: {entry.get('amount')}",
                                severity="error",
                            )
                        )

            # 消費税を計算して加算
            tax_8_percent = int(tax_totals["8%"] * 0.08 + 0.5)  # 小数点以下切り上げ
            tax_10_percent = int(tax_totals["10%"] * 0.1 + 0.5)  # 小数点以下切り上げ
            tax_unknown = int(tax_totals["unknown"] * 0.1 + 0.5)  # 不明な税率は10%と仮定
            
            # 税込み合計金額
            sum_with_tax = sum_amount + tax_8_percent + tax_10_percent + tax_unknown
            
            # 計算結果をログに出力
            logger.info(f"合計金額検証: 明細合計(税抜)={sum_amount:,}円")
            logger.info(f"税率8%の合計: {tax_totals['8%']:,}円, 消費税: {tax_8_percent:,}円")
            logger.info(f"税率10%の合計: {tax_totals['10%']:,}円, 消費税: {tax_10_percent:,}円")
            logger.info(f"税率不明の合計: {tax_totals['unknown']:,}円, 消費税(10%として): {tax_unknown:,}円")
            logger.info(f"明細合計(税込): {sum_with_tax:,}円, 合計金額: {total_amount:,}円")
            
            # 許容誤差（端数処理の違いによる誤差を許容）
            tolerance = 10
            
            if abs(total_amount - sum_with_tax) > tolerance:
                errors.append(
                    ValidationError(
                        field="total_amount",
                        message=f"合計金額が一致しません（明細合計(税込): {sum_with_tax:,}円, 合計金額: {total_amount:,}円）",
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
                # tax_rateを文字列に変換
                if tax_rate is not None:
                    tax_rate = str(tax_rate)
                if tax_rate and tax_rate not in valid_rates:
                    errors.append(
                        ValidationError(
                            field="tax_rate",
                            message=f"不正な税率です: {tax_rate}（有効な税率: {', '.join(valid_rates)}）",
                            severity="warning",
                        )
                    )

        return errors

    def _validate_customer_code_diversity(self, document: Dict[str, Any]) -> List[ValidationError]:
        """顧客コードの多様性検証（全て同じ顧客コードの場合はエラー）"""
        errors = []
        logger = logging.getLogger(__name__)
        
        # すべての顧客コードを収集
        customer_codes = []
        for customer in document.get("customers", []):
            customer_code = customer.get("customer_code")
            if customer_code:
                customer_codes.append(customer_code)
        
        # 顧客コードが存在しない場合はチェックしない
        if not customer_codes:
            return errors
            
        # ユニークな顧客コードの数を確認
        unique_codes = set(customer_codes)
        
        # 顧客コードが1種類しかない場合はエラー
        if len(unique_codes) == 1 and len(customer_codes) > 1:
            code = next(iter(unique_codes))
            logger.warning(f"すべての明細行で同じ顧客コード '{code}' が使用されています")
            errors.append(
                ValidationError(
                    field="customer_code",
                    message=f"すべての明細行で同じ顧客コード '{code}' が使用されています。複数の取引先がある場合は、それぞれ異なる顧客コードを設定してください。",
                    severity="error"
                )
            )
            
        return errors
