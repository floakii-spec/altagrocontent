import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import competitors, carousel, news, reports, voice, studio
from src.carousel.theme_suggester import generate_theme_suggestions

logger = logging.getLogger(__name__)


def _run_daily_suggestions():
    from src.database import get_session
    session = get_session()
    try:
        generate_theme_suggestions(session)
    except Exception as exc:
        logger.error("Daily suggestion job failed: %s", exc)
    finally:
        session.close()


scheduler = BackgroundScheduler()
scheduler.add_job(_run_daily_suggestions, "cron", hour=6, minute=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logger.info("APScheduler started")
    yield
    scheduler.shutdown(wait=False)
    logger.info("APScheduler stopped")


app = FastAPI(title="Agro Intel API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)
app.include_router(carousel.router)
app.include_router(news.router)
app.include_router(reports.router)
app.include_router(voice.router)
app.include_router(studio.router)


@app.get("/health")
def health():
    return {"status": "ok"}
