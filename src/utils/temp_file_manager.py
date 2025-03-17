import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import UploadFile


class TempFileManager:
    def __init__(self, temp_dir: str = "temp"):
        """一時ファイル管理クラスの初期化"""
        self.temp_dir = temp_dir
        self.uploads_dir = os.path.join(temp_dir, "uploads")
        self.images_dir = os.path.join(temp_dir, "images")
        self.processed_dir = os.path.join(temp_dir, "processed")

        # 必要なディレクトリの作成
        for directory in [
            self.temp_dir,
            self.uploads_dir,
            self.images_dir,
            self.processed_dir,
        ]:
            os.makedirs(directory, exist_ok=True)

    def generate_task_id(self) -> str:
        """一意のタスクIDを生成する"""
        return str(uuid.uuid4())

    def save_upload(self, file: UploadFile, task_id: str) -> str:
        """アップロードされたファイルを保存する"""
        file_path = os.path.join(self.uploads_dir, f"{task_id}.pdf")
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return file_path

    def save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """処理結果を一時保存する"""
        result_path = os.path.join(self.processed_dir, f"{task_id}.json")
        import json

        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """処理結果を取得する"""
        result_path = os.path.join(self.processed_dir, f"{task_id}.json")
        if not os.path.exists(result_path):
            return None

        import json

        with open(result_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_pdf_path(self, task_id: str) -> str:
        """PDFファイルのパスを取得する"""
        return os.path.join(self.uploads_dir, f"{task_id}.pdf")

    def get_image_path(self, task_id: str, detail_no: str) -> str:
        """明細画像のパスを取得する"""
        return os.path.join(self.images_dir, f"{task_id}_{detail_no}.jpg")

    def get_excel_path(self, task_id: str) -> str:
        """エクセルファイルのパスを取得する"""
        return os.path.join(self.processed_dir, f"{task_id}.xlsx")

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """古い一時ファイルを削除する"""
        now = datetime.now()
        count = 0

        for directory in [self.uploads_dir, self.images_dir, self.processed_dir]:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                if now - file_modified > timedelta(hours=max_age_hours):
                    try:
                        os.remove(file_path)
                        count += 1
                    except OSError:
                        pass

        return count
