from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import competitors

app = FastAPI(title="Agro Intel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(competitors.router)


@app.get("/health")
def health():
    return {"status": "ok"}
