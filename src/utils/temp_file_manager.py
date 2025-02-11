import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from utils.logger import get_logger

logger = get_logger(__name__)


class TempFileManager:
    """一時ファイル管理クラス"""

    def __init__(self, temp_dir: str):
        """
        初期化

        Args:
            temp_dir (str): 一時ディレクトリのパス
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        古い一時ファイルを削除する

        Args:
            max_age_hours (int, optional): 保持する最大時間（時間単位）. デフォルトは24時間.

        Returns:
            int: 削除されたファイル数
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            # 一時ディレクトリ内のすべてのファイルをチェック
            for item in self.temp_dir.glob("**/*"):
                if not item.is_file():
                    continue

                # ファイルの最終更新時刻を取得
                mtime = datetime.fromtimestamp(item.stat().st_mtime)

                # 古いファイルを削除
                if mtime < cutoff_time:
                    try:
                        item.unlink()
                        deleted_count += 1
                        logger.debug(f"一時ファイルを削除: {item}")
                    except Exception as e:
                        logger.warning(f"ファイルの削除に失敗: {item} - {e}")

            # 空のディレクトリを削除
            self._remove_empty_dirs()

            logger.info(f"一時ファイルのクリーンアップが完了: {deleted_count}件")
            return deleted_count

        except Exception as e:
            logger.error(f"クリーンアップでエラー: {e}", exc_info=True)
            raise

    def _remove_empty_dirs(self):
        """空のディレクトリを削除する"""
        try:
            for dirpath, dirnames, filenames in os.walk(self.temp_dir, topdown=False):
                if dirpath == str(self.temp_dir):
                    continue  # ルートディレクトリは削除しない

                if not dirnames and not filenames:
                    try:
                        os.rmdir(dirpath)
                        logger.debug(f"空のディレクトリを削除: {dirpath}")
                    except Exception as e:
                        logger.warning(f"ディレクトリの削除に失敗: {dirpath} - {e}")

        except Exception as e:
            logger.error(f"空ディレクトリの削除でエラー: {e}", exc_info=True)

    def get_file_list(self, pattern: str = "*") -> List[Path]:
        """
        一時ファイルの一覧を取得する

        Args:
            pattern (str, optional): 検索パターン. デフォルトは"*".

        Returns:
            List[Path]: ファイルパスのリスト
        """
        try:
            return list(self.temp_dir.glob(f"**/{pattern}"))
        except Exception as e:
            logger.error(f"ファイル一覧の取得でエラー: {e}", exc_info=True)
            raise

    def clear_all(self) -> int:
        """
        すべての一時ファイルを削除する

        Returns:
            int: 削除されたファイル数
        """
        try:
            # ディレクトリ内のすべてのファイルを削除
            deleted_count = 0
            for item in self.temp_dir.glob("**/*"):
                if item.is_file():
                    try:
                        item.unlink()
                        deleted_count += 1
                        logger.debug(f"一時ファイルを削除: {item}")
                    except Exception as e:
                        logger.warning(f"ファイルの削除に失敗: {item} - {e}")

            # 空のディレクトリを削除
            self._remove_empty_dirs()

            logger.info(f"一時ファイルの全削除が完了: {deleted_count}件")
            return deleted_count

        except Exception as e:
            logger.error(f"全削除でエラー: {e}", exc_info=True)
            raise


# 使用例:
"""
temp_manager = TempFileManager("/path/to/temp")

# 古いファイルのクリーンアップ
deleted_count = temp_manager.cleanup_old_files(max_age_hours=12)

# ファイル一覧の取得
files = temp_manager.get_file_list("*.pdf")

# すべてのファイルの削除
deleted_count = temp_manager.clear_all()
"""
