import os
import logging
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class APIClient:
    """FastAPIサーバーとの通信を管理するクライアントクラス"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Args:
            base_url (str): APIサーバーのベースURL
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def upload_document(self, file_path: str) -> Dict:
        """
        PDFファイルをアップロードする

        Args:
            file_path (str): アップロードするPDFファイルのパス

        Returns:
            Dict: アップロード結果
            {
                'status': 'success',
                'document_id': 'xxx',
                'message': '処理が完了しました'
            }

        Raises:
            RequestException: APIリクエストでエラーが発生した場合
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

            if not file_path.lower().endswith(".pdf"):
                raise ValueError("PDFファイルのみアップロード可能です")

            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "application/pdf")}
                response = self.session.post(
                    f"{self.base_url}/document/upload", files=files
                )
                response.raise_for_status()
                return response.json()

        except RequestException as e:
            logger.error(f"アップロード中にエラーが発生: {e}", exc_info=True)
            raise

    def get_processing_status(self, document_id: str) -> Dict:
        """
        ドキュメントの処理状態を取得する

        Args:
            document_id (str): ドキュメントID

        Returns:
            Dict: 処理状態
            {
                'status': 'processing',
                'progress': 50,
                'message': '処理中...'
            }
        """
        try:
            response = self.session.get(
                f"{self.base_url}/document/status/{document_id}"
            )
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            logger.error(f"状態取得中にエラーが発生: {e}", exc_info=True)
            raise

    def get_validation_result(self, document_id: str) -> Dict:
        """
        バリデーション結果を取得する

        Args:
            document_id (str): ドキュメントID

        Returns:
            Dict: バリデーション結果
            {
                'is_valid': bool,
                'errors': List[Dict],
                'warnings': List[Dict]
            }
        """
        try:
            response = self.session.get(
                f"{self.base_url}/document/validation/{document_id}"
            )
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            logger.error(f"バリデーション結果取得中にエラーが発生: {e}", exc_info=True)
            raise

    def get_detail_images(self, document_id: str, page: Optional[int] = None) -> Dict:
        """
        明細画像のパスリストを取得する

        Args:
            document_id (str): ドキュメントID
            page (Optional[int]): ページ番号（指定しない場合は全ページ）

        Returns:
            Dict: 画像パスのリスト
            {
                'images': List[str]
            }
        """
        try:
            params = {"page": page} if page is not None else None
            response = self.session.get(
                f"{self.base_url}/document/images/{document_id}", params=params
            )
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            logger.error(f"画像パス取得中にエラーが発生: {e}", exc_info=True)
            raise

    def download_file(self, document_id: str, output_path: str) -> str:
        """
        処理済みファイルをダウンロードする

        Args:
            document_id (str): ドキュメントID
            output_path (str): 保存先のパス

        Returns:
            str: ダウンロードしたファイルのパス
        """
        try:
            response = self.session.get(
                f"{self.base_url}/document/download/{document_id}", stream=True
            )
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return output_path

        except RequestException as e:
            logger.error(f"ファイルダウンロード中にエラーが発生: {e}", exc_info=True)
            raise
