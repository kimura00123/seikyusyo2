import json
import pandas as pd
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, create_model
import inspect

class StockInfo(BaseModel):
    carryover: int
    incoming: int
    w_value: int
    outgoing: int
    remaining: int
    total: int
    unit_price: int

    @classmethod
    def get_field_names(cls) -> List[str]:
        """モデルのフィールド名を取得"""
        return list(cls.model_fields.keys())

class QuantityInfo(BaseModel):
    quantity: int
    unit_price: Optional[int] = None

    @classmethod
    def get_field_names(cls) -> List[str]:
        """モデルのフィールド名を取得"""
        return list(cls.model_fields.keys())

class EntryDetail(BaseModel):
    no: str
    description: str
    tax_rate: str
    amount: str
    stock_info: Optional[StockInfo] = None
    quantity_info: Optional[QuantityInfo] = None
    date_range: Optional[str] = None
    page_no: int  # 追加：ページ番号

    @classmethod
    def get_base_field_names(cls) -> List[str]:
        """基本フィールド名を取得（ネストされたモデルを除く）"""
        return [
            name for name, field in cls.model_fields.items()
            if not isinstance(field.annotation, type)
            or not issubclass(field.annotation, BaseModel)
        ]

class CustomerEntry(BaseModel):
    customer_code: str
    customer_name: str
    department: str
    box_number: str
    entries: List[EntryDetail]

    @classmethod
    def get_base_field_names(cls) -> List[str]:
        """基本フィールド名を取得（Listフィールドを除く）"""
        return [
            name for name, field in cls.model_fields.items()
            if not str(field.annotation).startswith('typing.List')
        ]

class DocumentStructure(BaseModel):
    pdf_filename: str  # 追加：PDFファイル名（PDF全体）
    total_amount: str  # 追加：請求合計額（PDF全体）
    customers: List[CustomerEntry]


    @classmethod
    def get_base_field_names(cls) -> List[str]:
        return [
            name for name, field in cls.model_fields.items()
            if not str(field.annotation).startswith('typing.List')
        ]


def get_flattened_field_mapping() -> Dict[str, List[str]]:
    """
    各モデルのフィールド名をプレフィックス付きで取得

    Returns:
        Dict[str, List[str]]: カテゴリごとのフィールド名リスト
    """
    return {
        'document': DocumentStructure.get_base_field_names(),  # 追加：ドキュメント全体の情報
        'customer': CustomerEntry.get_base_field_names(),
        'entry': EntryDetail.get_base_field_names(),
        'stock': [f"stock_{field}" for field in StockInfo.get_field_names()],
        'quantity': [f"quantity_{field}" for field in QuantityInfo.get_field_names()]
    }

def flatten_customer_data(json_data: str) -> pd.DataFrame:
    """
    JSONデータをフラット化してDataFrameに変換

    Args:
        json_data (str): JSON形式の文字列データ

    Returns:
        pd.DataFrame: フラット化されたデータ
    """
    # JSONデータをパース
    data = DocumentStructure.parse_raw(json_data)
    flattened_data = []

    # フィールドマッピングを取得
    field_mapping = get_flattened_field_mapping()

    # ドキュメント全体の情報を取得
    doc_info = {
        field: getattr(data, field)
        for field in field_mapping['document']
    }


    # 各顧客のデータをフラット化
    for customer in data.customers:
        # 顧客の基本情報を取得
        base_info = {
            field: getattr(customer, field)
            for field in field_mapping['customer']
        }

        # ドキュメント情報を追加  # ← この行を追加
        base_info.update(doc_info)  # ← この行を追加

        # 各エントリーを処理
        for entry in customer.entries:
            entry_data = base_info.copy()

            # 基本エントリー情報を追加
            entry_data.update({
                field: getattr(entry, field)
                for field in field_mapping['entry']
                if hasattr(entry, field)
            })

            # 在庫情報を追加
            if entry.stock_info:
                stock_info = entry.stock_info.dict()
                entry_data.update({
                    f"stock_{k}": v
                    for k, v in stock_info.items()
                })

            # 数量情報を追加
            if entry.quantity_info:
                quantity_info = entry.quantity_info.dict()
                entry_data.update({
                    f"quantity_{k}": v
                    for k, v in quantity_info.items()
                })

            flattened_data.append(entry_data)

    # DataFrameに変換
    df = pd.DataFrame(flattened_data)

    # 列の順序を動的に生成
    column_order = []
    categories = ['document', 'customer', 'entry', 'stock', 'quantity']
    for category in categories:
        column_order.extend(field_mapping[category])

    # 存在する列のみを選択
    existing_columns = [col for col in column_order if col in df.columns]

    return df[existing_columns]

def main():
    """
    メイン処理
    """
    try:
        # JSONファイルを読み込む
        with open('processed_document.json', 'r', encoding='utf-8') as f:
            json_data = f.read()

        # データをフラット化してDataFrameに変換
        df = flatten_customer_data(json_data)

        # CSVファイルとして保存
        df.to_csv('customer_data1.csv', index=False, encoding='utf-8-sig')
        print("CSVファイルが生成されました: customer_data.csv")

        # データの概要を表示
        print("\nデータの概要:")
        print(f"総レコード数: {len(df)}")
        print("\n列一覧:")
        for col in df.columns:
            print(f"- {col}")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()