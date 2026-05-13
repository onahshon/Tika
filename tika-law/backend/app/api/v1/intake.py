from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.v1.dependencies import require_attorney_id
from backend.app.schemas.intake import LeadIntakeRequest, LeadQualificationResponse
from backend.app.services.lead_qualification import qualify_lead

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("/qualify", response_model=LeadQualificationResponse)
def qualify_intake(
    request: LeadIntakeRequest,
    attorney_id: str = Depends(require_attorney_id),
) -> LeadQualificationResponse:
    if request.attorney_id != attorney_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="attorney_id must match X-Attorney-Id.",
        )

    return qualify_lead(request)
