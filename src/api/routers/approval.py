from datetime import datetime
from typing import Optional

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ...utils.cosmos import CosmosDBClient
from ...utils.logger import get_logger
from ...models.approval import (
    ApprovalStatus,
    ApprovalHistory,
    ApprovalResponse,
    ApprovalStatusResponse,
)

logger = get_logger(__name__)
router = APIRouter()


async def get_cosmos_client():
    """CosmosDBクライアントの取得"""
    client = CosmosDBClient()
    return client


@router.post("/approvals/{task_id}/{detail_no}")
async def approve_detail(
    task_id: str,
    detail_no: str,
    user_id: str,
    cosmos_client: CosmosDBClient = Depends(get_cosmos_client),
) -> ApprovalResponse:
    """明細の承認"""
    try:
        logger.info(
            f"承認処理開始: task_id={task_id}, detail_no={detail_no}, user_id={user_id}"
        )

        # 承認状態の作成
        approval = ApprovalStatus(
            task_id=task_id,
            detail_no=detail_no,
            approved=True,
            approved_at=datetime.now(),
            approved_by=user_id,
        )

        # 承認状態の保存
        try:
            await cosmos_client.save_approval(approval)
            logger.info(f"承認状態を保存: {approval}")
        except Exception as e:
            logger.error(f"承認状態の保存に失敗: {e}", exc_info=True)
            raise

        # 承認履歴の保存
        history = ApprovalHistory(
            task_id=task_id,
            detail_no=detail_no,
            action="approve",
            timestamp=datetime.now(),
            user_id=user_id,
            reason="承認",
        )
        try:
            await cosmos_client.save_approval_history(history)
            logger.info(f"承認履歴を保存: {history}")
        except Exception as e:
            logger.error(f"承認履歴の保存に失敗: {e}", exc_info=True)
            raise

        response = ApprovalResponse(
            success=True,
            detail_no=detail_no,
            approved=True,
            approved_at=approval.approved_at,
            approved_by=user_id,
            message="承認が完了しました",
        )
        logger.info(f"承認処理完了: {response}")
        return response

    except Exception as e:
        logger.error(f"承認処理でエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/approvals/{task_id}/{detail_no}")
async def cancel_approval(
    task_id: str,
    detail_no: str,
    user_id: str,
    cosmos_client: CosmosDBClient = Depends(get_cosmos_client),
) -> ApprovalResponse:
    """承認の取り消し"""
    try:
        # 承認状態の削除
        success = await cosmos_client.delete_approval(task_id, detail_no)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"message": "承認状態が見つかりません"},
            )

        # 承認履歴の保存
        history = ApprovalHistory(
            task_id=task_id,
            detail_no=detail_no,
            action="cancel",
            timestamp=datetime.now(),
            user_id=user_id,
            reason="承認取り消し",
        )
        await cosmos_client.save_approval_history(history)

        return ApprovalResponse(
            success=True,
            detail_no=detail_no,
            approved=False,
            approved_at=None,
            approved_by=None,
            message="承認を取り消しました",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/{task_id}")
async def get_approval_status(
    task_id: str,
    detail_no: Optional[str] = None,
    cosmos_client: CosmosDBClient = Depends(get_cosmos_client),
) -> ApprovalStatusResponse:
    """承認状態の取得"""
    try:
        # 承認状態の取得
        approvals = await cosmos_client.get_approval_status(task_id, detail_no)

        return ApprovalStatusResponse(
            task_id=task_id,
            approved_details=approvals,
            total_details=len(approvals),
            approved_count=len([a for a in approvals if a.approved]),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/{task_id}/history")
async def get_approval_history(
    task_id: str,
    detail_no: Optional[str] = None,
    cosmos_client: CosmosDBClient = Depends(get_cosmos_client),
) -> list[ApprovalHistory]:
    """承認履歴の取得"""
    try:
        # 承認履歴の取得
        history = await cosmos_client.get_approval_history(task_id, detail_no)
        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
