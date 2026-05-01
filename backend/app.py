from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import analyze, reports, assistant, pdf, export, tracker, usage

app = FastAPI(title="PPC Master Tool API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
app.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
app.include_router(export.router, prefix="/export", tags=["export"])
app.include_router(tracker.router)
app.include_router(usage.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
