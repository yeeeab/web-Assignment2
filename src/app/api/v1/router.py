from fastapi import APIRouter
from .health import router as health
from .auth import router as auth
from .items import router as items
from .bids import router as bids
from .categories import router as categories
from .watches import router as watches
from .orders import router as orders
from .admin import router as admin
from .stats import router as stats
from .users import router as users

router.include_router(users, tags=["users"])
router = APIRouter(prefix="/api/v1")
router.include_router(health, tags=["health"])
router.include_router(auth, tags=["auth"])
router.include_router(items, tags=["items"])
router.include_router(bids, tags=["bids"])
router.include_router(categories, tags=["categories"])
router.include_router(watches, tags=["watches"])
router.include_router(orders, tags=["orders"])
router.include_router(admin, tags=["admin"])
router.include_router(stats, tags=["stats"])