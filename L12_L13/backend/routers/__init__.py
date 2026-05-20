from fastapi import APIRouter

from .auth import router as auth_router
from .menu import router as menu_router
from .reservations import router as reservations_router
from .staff import router as staff_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(menu_router)
api_router.include_router(reservations_router)
api_router.include_router(staff_router)