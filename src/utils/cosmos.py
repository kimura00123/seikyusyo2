import os
import uuid
from typing import Optional, List
from datetime import datetime

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from src.models.approval import ApprovalStatus, ApprovalHistory
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)


class CosmosDBClient:
    """CosmosDBクライアント"""

    def __init__(self):
        # 設定クラスから読み込み
        settings = get_settings()
        uri = settings.COSMOS_DB_URI
        key = settings.COSMOS_DB_KEY
        database_name = settings.COSMOS_DB_DATABASE_NAME
        container_name = settings.COSMOS_DB_CONTAINER_NAME

        logger.debug(
            f"CosmosDB設定: URI={uri}, DB={database_name}, Container={container_name}"
        )

        if not all([uri, key, database_name, container_name]):
            missing = [
                name
                for name, value in {
                    "COSMOS_DB_URI": uri,
                    "COSMOS_DB_KEY": key,
                    "COSMOS_DB_DATABASE_NAME": database_name,
                    "COSMOS_DB_CONTAINER_NAME": container_name,
                }.items()
                if not value
            ]
            error_msg = (
                f"Required environment variables are not set: {', '.join(missing)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # CosmosDBクライアントの初期化
            self.client = CosmosClient(uri, credential=key)

            # データベースの作成（存在しない場合）
            logger.debug(f"データベースの作成を試行: {database_name}")
            self.database = self.client.create_database_if_not_exists(id=database_name)
            logger.info(f"データベースの準備完了: {database_name}")

            # コンテナの作成（存在しない場合）
            logger.debug(f"コンテナの作成を試行: {container_name}")
            self.container = self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(
                    path="/task_id"
                ),  # パーティションキーは/task_idのまま
            )
            logger.info(f"コンテナの準備完了: {container_name}")

            logger.info("CosmosDBクライアントの初期化が完了しました")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDBクライアントの初期化に失敗: {e}", exc_info=True)
            raise

    async def get_approval_status(
        self, task_id: str, detail_no: Optional[str] = None
    ) -> List[ApprovalStatus]:
        """承認状態を取得"""
        try:
            if detail_no:
                # 特定の明細の承認状態を取得
                query = """
                    SELECT * FROM c 
                    WHERE c.type = 'approval_status' 
                    AND c.task_id = @task_id 
                    AND c.detail_no = @detail_no
                """
                parameters = [
                    {"name": "@task_id", "value": task_id},
                    {"name": "@detail_no", "value": detail_no},
                ]
                logger.debug(
                    f"特定の明細の承認状態を取得: task_id={task_id}, detail_no={detail_no}"
                )
            else:
                # タスクの全明細の承認状態を取得
                query = """
                    SELECT * FROM c 
                    WHERE c.type = 'approval_status' 
                    AND c.task_id = @task_id
                """
                parameters = [{"name": "@task_id", "value": task_id}]
                logger.debug(f"タスクの全明細の承認状態を取得: task_id={task_id}")

            results = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            )
            approvals = []
            for item in results:
                # datetimeを文字列から変換
                if "approved_at" in item and item["approved_at"]:
                    item["approved_at"] = datetime.fromisoformat(item["approved_at"])
                approvals.append(
                    ApprovalStatus(**{k: v for k, v in item.items() if k != "type"})
                )
            logger.info(f"承認状態を取得: {len(approvals)}件")
            return approvals
        except Exception as e:
            logger.error(f"承認状態の取得に失敗: {e}", exc_info=True)
            raise Exception(f"Failed to get approval status: {str(e)}")

    async def save_approval(self, approval: ApprovalStatus) -> bool:
        """承認状態を保存"""
        try:
            # ドキュメントタイプを追加
            document = {
                "type": "approval_status",
                "id": f"{approval.task_id}_{approval.detail_no}",
                "task_id": approval.task_id,
                "detail_no": approval.detail_no,
                "approved": approval.approved,
                "approved_at": (
                    approval.approved_at.isoformat() if approval.approved_at else None
                ),  # datetimeを文字列に変換
                "approved_by": approval.approved_by,
            }
            logger.debug(f"承認状態のドキュメントを作成: {document}")

            # 既存の承認状態を確認
            try:
                existing = await self.get_approval_status(
                    approval.task_id, approval.detail_no
                )
                if existing:
                    # 更新
                    logger.debug(f"既存の承認状態を更新: {document['id']}")
                    self.container.replace_item(
                        item=document["id"],
                        body=document,
                    )
                else:
                    # 新規作成
                    logger.debug(f"新規の承認状態を作成: {document['id']}")
                    self.container.create_item(body=document)
            except CosmosResourceNotFoundError:
                # 新規作成
                logger.debug(f"新規の承認状態を作成（リソースなし）: {document['id']}")
                self.container.create_item(body=document)

            logger.info(
                f"承認状態を保存: task_id={approval.task_id}, detail_no={approval.detail_no}"
            )
            return True
        except Exception as e:
            logger.error(f"承認状態の保存に失敗: {e}", exc_info=True)
            raise Exception(f"Failed to save approval: {str(e)}")

    async def delete_approval(self, task_id: str, detail_no: str) -> bool:
        """承認状態を削除"""
        try:
            document_id = f"{task_id}_{detail_no}"
            self.container.delete_item(
                item=document_id,
                partition_key=task_id,  # パーティションキーを指定
            )
            return True
        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            raise Exception(f"Failed to delete approval: {str(e)}")

    async def save_approval_history(self, history: ApprovalHistory) -> bool:
        """承認履歴を保存"""
        try:
            # ドキュメントタイプを追加
            document = {
                "type": "approval_history",
                "id": f"{history.task_id}_{history.detail_no}_{history.timestamp.isoformat()}",
                "task_id": history.task_id,
                "detail_no": history.detail_no,
                "action": history.action,
                "timestamp": history.timestamp.isoformat(),  # datetimeを文字列に変換
                "user_id": history.user_id,
                "reason": history.reason,
            }
            self.container.create_item(body=document)
            return True
        except Exception as e:
            raise Exception(f"Failed to save approval history: {str(e)}")

    async def get_approval_history(
        self, task_id: str, detail_no: Optional[str] = None
    ) -> List[ApprovalHistory]:
        """承認履歴を取得"""
        try:
            if detail_no:
                # 特定の明細の承認履歴を取得
                query = """
                    SELECT * FROM c 
                    WHERE c.type = 'approval_history' 
                    AND c.task_id = @task_id 
                    AND c.detail_no = @detail_no 
                    ORDER BY c.timestamp DESC
                """
                parameters = [
                    {"name": "@task_id", "value": task_id},
                    {"name": "@detail_no", "value": detail_no},
                ]
            else:
                # タスクの全明細の承認履歴を取得
                query = """
                    SELECT * FROM c 
                    WHERE c.type = 'approval_history' 
                    AND c.task_id = @task_id 
                    ORDER BY c.timestamp DESC
                """
                parameters = [{"name": "@task_id", "value": task_id}]

            results = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                )
            )
            histories = []
            for item in results:
                # datetimeを文字列から変換
                if "timestamp" in item and item["timestamp"]:
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                histories.append(
                    ApprovalHistory(**{k: v for k, v in item.items() if k != "type"})
                )
            return histories
        except Exception as e:
            raise Exception(f"Failed to get approval history: {str(e)}")
