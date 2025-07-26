from typing import Annotated, Optional, Literal
import cloudinary
import cloudinary.uploader

from sqlalchemy.orm import Session

from api.v1.models.user import User
from fastapi import status, APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.encoders import jsonable_encoder

from api.utils.success_response import success_response
from api.core.config import settings
from api.v1.services.user import user_service
from api.v1.schemas.user import UserUpdate

from api.db.database import get_db

cloudinary.config(
    cloud_name = settings.CLOUD_NAME,
    api_key = settings.API_KEY,
    api_secret = settings.API_SECRETS
)

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        result = cloudinary.uploader.upload(file.file, folder="testa_profile_image")
        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    

@router.patch("/update", status_code=status.HTTP_200_OK)
def update_current_user(
    user_id: str,
    current_user : Annotated[User , Depends(user_service.get_current_user)],
    schema: UserUpdate,
    db : Session = Depends(get_db),
):
    user = user_service.update(db=db, schema=schema, id=user_id, current_user=current_user)

    return success_response(
        status_code=status.HTTP_200_OK,
        message='User Updated Successfully',
        data= jsonable_encoder(
            user,
            exclude=['password', 'is_admin', 'is_verified', 'created_at', 'is_active']
        )
    )


