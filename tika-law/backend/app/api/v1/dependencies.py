from fastapi import Header, HTTPException, status


def require_attorney_id(
    x_attorney_id: str | None = Header(default=None, alias="X-Attorney-Id"),
) -> str:
    if not x_attorney_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Attorney-Id header is required.",
        )

    return x_attorney_id
