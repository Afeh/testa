from fastapi import APIRouter

from api.v1.routes.auth import router as auth_router
from api.v1.routes.profile import router as profile_router
from api.v1.routes.admin import router as admin_router
from api.v1.routes.exam import router as exam_routes
from api.v1.routes.verification import router as verification_routes

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(profile_router)
api_router.include_router(admin_router)
api_router.include_router(exam_routes)
api_router.include_router(verification_routes)