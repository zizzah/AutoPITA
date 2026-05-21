import asyncio
import sys


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings
from app.db.session import engine
from sqlalchemy import text
from app.core.exceptions import AutoPITAException, autopita_exception_handler
from app.api.v1.router import router as api_router


settings = get_settings()





@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    print("✅ Database connection successful")
    yield
    await engine.dispose()
    print("🛑 Database connection closed")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan
)


app.add_exception_handler(AutoPITAException, autopita_exception_handler)
app.include_router(api_router)




@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment
    }