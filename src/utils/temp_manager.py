import os
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import json

class TempManager:
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)

    def generate_task_id(self) -> str:
        """タスクIDを生成"""
        return str(uuid.uuid4())

    def get_image_path(self, task_id: str, detail_no: str) -> str:
        """明細画像の一時保存パスを取得"""
        image_dir = self.temp_dir / task_id / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        return str(image_dir / f"detail_{detail_no}.jpg")

    def get_pdf_path(self, task_id: str) -> str:
        """PDFファイルの一時保存パスを取得"""
        return str(self.temp_dir / task_id / "document.pdf")

    def get_excel_path(self, task_id: str) -> str:
        """Excelファイルの一時保存パスを取得"""
        return str(self.temp_dir / task_id / "output.xlsx")

    def save_upload(self, file: Any, task_id: str) -> str:
        """アップロードされたファイルを保存"""
        pdf_path = self.get_pdf_path(task_id)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        # 元のファイル名を保存
        original_filename = file.filename
        filename_path = self.temp_dir / task_id / "original_filename.txt"
        with open(filename_path, "w", encoding="utf-8") as f:
            f.write(original_filename)
        
        with open(pdf_path, "wb") as buffer:
            buffer.write(file.file.read())
        return pdf_path

    def get_original_filename(self, task_id: str) -> str:
        """元のファイル名を取得"""
        filename_path = self.temp_dir / task_id / "original_filename.txt"
        if not filename_path.exists():
            return "document.pdf"  # デフォルト値
        with open(filename_path, "r", encoding="utf-8") as f:
            return f.read().strip()

    def save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """処理結果を保存"""
        result_path = self.temp_dir / task_id / "result.json"
        os.makedirs(result_path.parent, exist_ok=True)
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """処理結果を取得"""
        result_path = self.temp_dir / task_id / "result.json"
        if not result_path.exists():
            return None
        with open(result_path, encoding="utf-8") as f:
            return json.load(f)

# シングルトンインスタンスを作成
temp_manager = TempManager() 