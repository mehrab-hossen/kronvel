from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import get_remediation_service
from app.core.exceptions import ActionBlockedError
from app.core.security import verify_api_key
from app.models.action_audit import ActionAudit
from app.services.remediation_service import RemediationService

router = APIRouter()


class RemediationRequest(BaseModel):
    action: str
    node: str
    dry_run: bool | None = None
    requested_by: str = "operator"


@router.post("/remediation/execute", response_model=ActionAudit, dependencies=[Depends(verify_api_key)])
async def execute_remediation(
    request: RemediationRequest,
    service: RemediationService = Depends(get_remediation_service),
) -> ActionAudit:
    try:
        return await service.execute(
            action=request.action,
            node=request.node,
            dry_run=request.dry_run,
            requested_by=request.requested_by,
        )
    except ActionBlockedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/remediation/history", response_model=list[ActionAudit])
async def remediation_history(
    node: str | None = Query(default=None),
    service: RemediationService = Depends(get_remediation_service),
) -> list[ActionAudit]:
    return await service.get_history(node=node)

