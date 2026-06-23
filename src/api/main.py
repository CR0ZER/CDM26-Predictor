from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import predict, matches


app = FastAPI(title="CdM 2026 Predictor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/api", tags=["predict"])
app.include_router(matches.router, prefix="/api", tags=["matches"])


@app.get("/health")
def health():
    return {"status": "ok"}