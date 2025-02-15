"""
一時ファイル管理機能のテスト
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from src.utils.temp_file_manager import TempFileManager


@pytest.fixture
def temp_dir(tmp_path):
    """テスト用の一時ディレクトリを提供"""
    return tmp_path / "temp"


@pytest.fixture
def manager(temp_dir):
    """TempFileManagerインスタンスを提供"""
    return TempFileManager(str(temp_dir))


@pytest.fixture
def sample_files(temp_dir):
    """テスト用のサンプルファイルを作成"""
    # ディレクトリ構造を作成
    (temp_dir / "dir1").mkdir(parents=True)
    (temp_dir / "dir1/subdir").mkdir()
    (temp_dir / "dir2").mkdir()

    # ファイルを作成
    files = [
        temp_dir / "file1.txt",
        temp_dir / "file2.pdf",
        temp_dir / "dir1/file3.txt",
        temp_dir / "dir1/subdir/file4.pdf",
        temp_dir / "dir2/file5.txt",
    ]

    for file in files:
        file.write_text("test content")

    return files


def test_initialization(temp_dir):
    """初期化のテスト"""
    # 存在しないディレクトリの場合
    manager = TempFileManager(str(temp_dir))
    assert temp_dir.exists()
    assert temp_dir.is_dir()

    # 既存のディレクトリの場合
    temp_dir.mkdir(exist_ok=True)
    manager = TempFileManager(str(temp_dir))
    assert temp_dir.exists()


def test_get_file_list(manager, sample_files):
    """ファイル一覧取得のテスト"""
    # すべてのファイル（ディレクトリを除外）
    files = [f for f in manager.get_file_list() if f.is_file()]
    assert len(files) == 5
    assert all(f.exists() and f.is_file() for f in files)

    # パターンマッチング
    pdf_files = manager.get_file_list("*.pdf")
    assert len(pdf_files) == 2
    assert all(f.suffix == ".pdf" for f in pdf_files)

    txt_files = manager.get_file_list("*.txt")
    assert len(txt_files) == 3
    assert all(f.suffix == ".txt" for f in txt_files)


def test_cleanup_old_files(manager, sample_files, monkeypatch):
    """古いファイルのクリーンアップテスト"""
    # ファイルの更新時刻を設定
    old_time = datetime.now() - timedelta(hours=25)
    new_time = datetime.now() - timedelta(minutes=30)

    # 一部のファイルを古い時刻に設定
    old_files = sample_files[:2]  # file1.txt, file2.pdf
    new_files = sample_files[2:]  # その他のファイル

    for file in old_files:
        os.utime(file, (old_time.timestamp(), old_time.timestamp()))
    for file in new_files:
        os.utime(file, (new_time.timestamp(), new_time.timestamp()))

    # クリーンアップを実行（24時間以上経過したファイルを削除）
    deleted_count = manager.cleanup_old_files(max_age_hours=24)

    # 結果の検証
    assert deleted_count == 2  # 2つの古いファイルが削除される
    assert not any(f.exists() for f in old_files)  # 古いファイルは削除される
    assert all(f.exists() for f in new_files)  # 新しいファイルは残る


def test_remove_empty_dirs(manager, sample_files):
    """空ディレクトリの削除テスト"""
    # すべてのファイルを削除
    for file in sample_files:
        file.unlink()

    # 空ディレクトリの削除を実行（複数回実行して、深い階層から削除）
    for _ in range(3):  # サブディレクトリの最大深さ分繰り返す
        manager._remove_empty_dirs()

    # 結果の検証（削除の順序を考慮）
    paths = [
        manager.temp_dir / "dir1" / "subdir",
        manager.temp_dir / "dir1",
        manager.temp_dir / "dir2",
    ]
    assert all(not p.exists() for p in paths)  # すべてのディレクトリが削除されている
    assert manager.temp_dir.exists()  # ルートディレクトリは残る


def test_clear_all(manager, sample_files):
    """全ファイル削除のテスト"""
    # すべてのファイルを削除
    deleted_count = manager.clear_all()

    # 結果の検証
    assert deleted_count == 5  # すべてのファイルが削除される
    assert not any(f.exists() for f in sample_files)  # ファイルが存在しないことを確認
    assert manager.temp_dir.exists()  # ルートディレクトリは残る

    # ディレクトリの削除を確認（深い階層から順に）
    import time

    time.sleep(0.1)  # ディレクトリの削除を待つ

    # 削除の確認
    assert not (manager.temp_dir / "dir1" / "subdir").exists()  # 最も深い階層から確認
    assert not (manager.temp_dir / "dir1").exists()  # 中間階層
    assert not (manager.temp_dir / "dir2").exists()  # トップレベル


def test_error_handling(manager):
    """エラーハンドリングのテスト"""
    # 無効なパスでの初期化（Windowsで無効な文字を含むパス）
    with pytest.raises(OSError):
        TempFileManager("invalid/path/*:<>")

    # 権限エラー
    test_dir = manager.temp_dir / "readonly"
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test.txt"
    test_file.write_text("test")

    # 読み取り専用に設定（Windowsの場合は特別な処理）
    if os.name == "nt":
        import stat

        os.chmod(test_file, stat.S_IREAD)
        os.chmod(test_dir, stat.S_IREAD)
    else:
        test_dir.chmod(0o444)
        test_file.chmod(0o444)

    # 削除を試みる
    with pytest.raises(
        (PermissionError, OSError)
    ):  # WindowsとUNIXで異なるエラーが発生する可能性
        manager.clear_all()

    # 後始末
    if os.name == "nt":
        os.chmod(test_file, stat.S_IWRITE)
        os.chmod(test_dir, stat.S_IWRITE | stat.S_IEXEC)
    else:
        test_file.chmod(0o666)
        test_dir.chmod(0o777)
    test_file.unlink(missing_ok=True)
    test_dir.rmdir()


def test_file_pattern_matching(manager, sample_files):
    """ファイルパターンマッチングのテスト"""
    # 存在しないパターン
    files = manager.get_file_list("*.xyz")
    assert len(files) == 0

    # ワイルドカードパターン
    files = manager.get_file_list("file*.txt")
    assert len(files) == 3

    # サブディレクトリ内のファイル
    files = manager.get_file_list("**/file*.pdf")
    assert len(files) == 2


def test_concurrent_modification(manager, sample_files):
    """並行修正のテスト"""

    # クリーンアップ中にファイルが削除された場合
    def remove_file():
        sample_files[0].unlink()

    # ファイルを削除してからクリーンアップを実行
    remove_file()
    deleted_count = manager.cleanup_old_files()
    assert deleted_count == 0  # 既に削除されているファイルはカウントされない
