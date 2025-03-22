import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import json
from datetime import datetime, timedelta
from src.utils.logger import get_logger

logger = get_logger(__name__)

class TempManager:
    """一時ファイル管理クラス"""
    
    def __init__(self):
        self._temp_dir = None
    
    @property
    def temp_dir(self) -> Path:
        """一時ディレクトリのパスを取得"""
        if self._temp_dir is None:
            raise ValueError("一時ディレクトリが設定されていません")
        return self._temp_dir
    
    @temp_dir.setter
    def temp_dir(self, value):
        """一時ディレクトリのパスを設定"""
        # 文字列の場合はPathオブジェクトに変換
        if isinstance(value, str):
            value = Path(value)
        
        # ディレクトリが存在しない場合は作成
        if not value.exists():
            value.mkdir(parents=True, exist_ok=True)
            logger.info(f"一時ディレクトリを作成しました: {value}")
        
        self._temp_dir = value
    
    def create_temp_file(self, filename: str, content: bytes) -> Path:
        """一時ファイルを作成する"""
        file_path = self.temp_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path
    
    def create_temp_directory(self, dirname: str) -> Path:
        """一時ディレクトリを作成する"""
        dir_path = self.temp_dir / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    def cleanup_old_files(self, hours: int = 24) -> int:
        """
        指定時間以上経過した一時ファイルを削除する
        
        Args:
            hours: 経過時間（時間単位）
            
        Returns:
            削除したファイル数
        """
        try:
            logger.info(f"一時ファイルのクリーンアップを開始: {hours}時間以上経過したファイルを削除")
            
            # 現在時刻から指定時間前の時刻を計算
            cutoff_time = time.time() - (hours * 3600)
            count = 0
            
            # 一時ディレクトリ内のすべてのファイルとディレクトリをチェック
            for task_dir in self.temp_dir.glob("*"):
                try:
                    # ファイルの最終更新時刻を取得
                    mtime = task_dir.stat().st_mtime
                    
                    # 指定時間以上経過している場合は削除
                    if mtime < cutoff_time:
                        if task_dir.is_dir():
                            shutil.rmtree(task_dir)
                        else:
                            task_dir.unlink()
                        count += 1
                except Exception as e:
                    logger.warning(f"ファイル削除でエラー: {task_dir} - {e}")
            
            logger.info(f"一時ファイルのクリーンアップが完了: {count}件")
            return count
            
        except Exception as e:
            logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
            return 0

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
            if hasattr(file.file, "read"):
                buffer.write(file.file.read())
            else:
                buffer.write(file.file)
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

# シングルトンインスタンス
temp_manager = TempManager()

# 後方互換性のためのエイリアス
class TempFileManager:
    """後方互換性のためのラッパークラス"""
    
    @staticmethod
    def get_temp_dir() -> Path:
        """一時ディレクトリのパスを取得"""
        return temp_manager.temp_dir
    
    @staticmethod
    def create_temp_file(filename: str, content: bytes) -> Path:
        """一時ファイルを作成する"""
        return temp_manager.create_temp_file(filename, content)
    
    @staticmethod
    def create_temp_directory(dirname: str) -> Path:
        """一時ディレクトリを作成する"""
        return temp_manager.create_temp_directory(dirname)
    
    @staticmethod
    def cleanup_old_files(hours: int = 24) -> int:
        """指定時間以上経過した一時ファイルを削除する"""
        return temp_manager.cleanup_old_files(hours) 