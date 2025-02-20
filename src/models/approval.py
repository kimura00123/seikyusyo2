from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class ApprovalStatus(BaseModel):
    """明細の承認状態を表すモデル"""

    detail_no: str
    approved: bool
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    task_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "detail_no": "001",
                "approved": True,
                "approved_at": "2025-02-20T10:00:00",
                "approved_by": "user123",
                "task_id": "task_001",
            }
        }


class ApprovalHistory(BaseModel):
    """承認履歴を表すモデル"""

    detail_no: str
    action: Literal["approve", "cancel"]
    timestamp: datetime
    user_id: str
    task_id: str
    reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "detail_no": "001",
                "action": "approve",
                "timestamp": "2025-02-20T10:00:00",
                "user_id": "user123",
                "task_id": "task_001",
                "reason": "承認済み",
            }
        }


class ApprovalResponse(BaseModel):
    """承認APIのレスポンスモデル"""

    success: bool
    detail_no: str
    approved: bool
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "detail_no": "001",
                "approved": True,
                "approved_at": "2025-02-20T10:00:00",
                "approved_by": "user123",
                "message": "承認が完了しました",
            }
        }


class ApprovalStatusResponse(BaseModel):
    """承認状態取得APIのレスポンスモデル"""

    task_id: str
    approved_details: list[ApprovalStatus]
    total_details: int
    approved_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "approved_details": [
                    {
                        "detail_no": "001",
                        "approved": True,
                        "approved_at": "2025-02-20T10:00:00",
                        "approved_by": "user123",
                        "task_id": "task_001",
                    }
                ],
                "total_details": 10,
                "approved_count": 1,
            }
        }
