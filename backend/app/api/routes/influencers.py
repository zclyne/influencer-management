from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.influencers.schemas import ManualInfluencerInput
from app.services.influencers import InfluencerService

router = APIRouter(prefix="/influencers", tags=["influencers"])


@router.post("/manual", status_code=201)
def create_manual_influencer(
    payload: ManualInfluencerInput,
    db: Annotated[Session, Depends(get_db)],
    merge_if_matched: bool = False,
) -> dict[str, object]:
    influencer = InfluencerService(db).manual_create(
        payload, merge_if_matched=merge_if_matched
    )
    return {
        "id": influencer.id,
        "display_name": influencer.display_name,
        "platform_count": len(influencer.platforms),
        "contact_count": len(influencer.contacts),
    }
