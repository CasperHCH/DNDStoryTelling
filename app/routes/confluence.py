from fastapi import APIRouter, Depends, HTTPException
from atlassian import Confluence
from app.models.user import User
from app.auth.auth_handler import get_current_user

router = APIRouter(prefix="/confluence", tags=["confluence"])

@router.post("/publish")
async def publish_to_confluence(
    content: str,
    title: str,
    parent_id: str,
    current_user: User = Depends(get_current_user)
):
    if not all([current_user.confluence_api_token, current_user.confluence_url]):
        raise HTTPException(
            status_code=400,
            detail="Confluence credentials not configured"
        )
    
    confluence = Confluence(
        url=current_user.confluence_url,
        token=current_user.confluence_api_token
    )
    
    try:
        page = confluence.create_page(
            space="YOUR_SPACE_KEY",
            title=title,
            body=content,
            parent_id=parent_id,
            type="page"
        )
        return {"page_id": page['id'], "url": page['_links']['base'] + page['_links']['webui']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))