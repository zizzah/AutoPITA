from fastapi import APIRouter
from app.api.v1 import auth
from app.api.v1 import transactions
from app.api.v1 import tax
from app.api.v1 import chat
from app.api.v1 import filing




router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(transactions.router)
router.include_router(tax.router)
router.include_router(chat.router)
router.include_router(filing.router)


