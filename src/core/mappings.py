import re

# 商品名から業務区分・業務内容への直接マッピング
product_type_mapping = {
    "保管料 文書箱": {"type": "保管", "detail": "保管"},
    "荷役料 - 新規入庫 文書箱": {"type": "荷役", "detail": "新規入庫"},
    "荷役料 - 入庫 文書箱": {"type": "荷役", "detail": "入庫"}, # 必要に応じて追加
    "荷役料 - 出庫 文書箱": {"type": "荷役", "detail": "出庫"},
    "荷役料 - 永久出庫 文書箱": {"type": "荷役", "detail": "永久出庫"},
    "運搬料 - 寺田便 文書箱": {"type": "運搬", "detail": "入出庫"},
    "A4文書用ダンボール": {"type": "運搬", "detail": "段ボール"},
    "廃棄手数料 文書箱": {"type": "運搬", "detail": "廃棄"}
}

# 商品名識別のための正規表現パターンリスト (具体的なパターンが先に評価されるように順序に注意)
# 各要素は (コンパイル済み正規表現オブジェクト, 対応する情報辞書) のタプル
regex_patterns = [
    # より具体的なパターンを先に記述
    (re.compile(r'保管料.*文書箱', re.IGNORECASE), {"type": "保管", "detail": "保管"}),
    (re.compile(r'荷役料\s*-\s*新規入庫.*文書箱', re.IGNORECASE), {"type": "荷役", "detail": "新規入庫"}),
    (re.compile(r'荷役料\s*-\s*入庫.*文書箱', re.IGNORECASE), {"type": "荷役", "detail": "入庫"}),
    (re.compile(r'荷役料\s*-\s*出庫.*文書箱', re.IGNORECASE), {"type": "荷役", "detail": "出庫"}),
    (re.compile(r'荷役料\s*-\s*永久出庫.*文書箱', re.IGNORECASE), {"type": "荷役", "detail": "永久出庫"}),
    (re.compile(r'運搬料\s*-\s*寺田便.*文書箱', re.IGNORECASE), {"type": "運搬", "detail": "入出庫"}),
    (re.compile(r'廃棄手数料.*文書箱', re.IGNORECASE), {"type": "運搬", "detail": "廃棄"}),
    (re.compile(r'A4文書用ダンボール|段ボール', re.IGNORECASE), {"type": "運搬", "detail": "段ボール"}),

    # より一般的なパターンを後に記述
    (re.compile(r'保管料', re.IGNORECASE), {"type": "保管", "detail": "保管"}),
    (re.compile(r'荷役料', re.IGNORECASE), {"type": "荷役", "detail": "荷役"}), # 一般的な荷役料
    (re.compile(r'運搬料', re.IGNORECASE), {"type": "運搬", "detail": "運搬"}), # 一般的な運搬料
    (re.compile(r'廃棄手数料', re.IGNORECASE), {"type": "運搬", "detail": "廃棄"}), # 一般的な廃棄
] 