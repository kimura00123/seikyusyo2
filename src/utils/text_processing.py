from typing import Optional
import re


def preprocess_text_for_detail_numbers(text: str) -> str:
    """
    明細番号の改行などのパターンを前処理して修正する
    structuring.py と image_processor.py で共通利用する関数
    
    Args:
        text: 処理対象のテキスト
        
    Returns:
        前処理されたテキスト
    """
    # 「No」と番号が改行で分かれているパターンを修正
    # 例: 「No\n32」→「No32」
    text = re.sub(r'No\s*[\r\n]+\s*(\d+)', r'No\1', text)
    
    # 「No.」と番号が改行で分かれているパターンを修正
    text = re.sub(r'No\.\s*[\r\n]+\s*(\d+)', r'No.\1', text)
    
    # 他の類似パターンの修正
    text = re.sub(r'Number\s*[\r\n]+\s*(\d+)', r'Number\1', text)
    text = re.sub(r'番号\s*[\r\n]+\s*(\d+)', r'番号\1', text)
    
    return text


def is_detail_number(text: str) -> Optional[str]:
    """
    明細番号かどうかを判定する
    structuring.py と image_processor.py で共通利用する関数
    
    Args:
        text: 検証するテキスト
        
    Returns:
        明細番号が見つかった場合はその番号、そうでなければNone
    """
    # 事前に前処理を適用
    text = preprocess_text_for_detail_numbers(text)
    
    patterns = [
        r"^No\.?\s*(\d+)\s*$",  # No.10 or No10
        r"^\s*(\d+)\s*$",        # 10
        r"^No\s*[.:]?\s*(\d+)",  # No: 10 or No. 10 with possible trailing text
        r"^\s*(\d+)\s*[.:]\s*",  # 10: or 10. with possible trailing text
        r"^\s*[(]?(\d+)[)]?\s*$" # (10) or 10 with possible parentheses
    ]

    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None 