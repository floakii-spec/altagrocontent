import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import competitors, carousel, news, reports, voice, studio, intelligence
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


def _run_daily_intelligence():
    from src.database import get_session
    from src.models import Post, PostIntelligence
    from src.analyzer.post_intelligence import analyze_post_intelligence
    session = get_session()
    try:
        analyzed_ids = [r[0] for r in session.query(PostIntelligence.post_id).all()]
        q = session.query(Post)
        if analyzed_ids:
            q = q.filter(Post.id.notin_(analyzed_ids))
        posts = q.limit(50).all()
        for post in posts:
            try:
                analyze_post_intelligence(post, session)
            except Exception as exc:
                logger.error("Daily intelligence job failed for post %s: %s", post.id, exc)
        logger.info("Daily intelligence job processed %d posts", len(posts))
    except Exception as exc:
        logger.error("Daily intelligence job failed: %s", exc)
    finally:
        session.close()


scheduler = BackgroundScheduler()
scheduler.add_job(_run_daily_suggestions, "cron", hour=6, minute=0)
scheduler.add_job(_run_daily_intelligence, "cron", hour=7, minute=0)


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
app.include_router(intelligence.router)


@app.get("/health")
def health():
    return {"status": "ok"}
