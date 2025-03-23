from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .routers.document import router as document_router
from main import app

app = FastAPI(title="請求書構造化システム")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """ルートパスへのアクセスをAPIドキュメントにリダイレクト"""
    return RedirectResponse(url="/docs")


app.include_router(document_router)
