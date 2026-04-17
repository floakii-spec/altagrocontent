from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors, carousel, news

app = FastAPI(title="Agro Intel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)
app.include_router(carousel.router)
app.include_router(news.router)


@app.get("/health")
def health():
    return {"status": "ok"}
