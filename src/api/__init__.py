from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .routers.document import router as document_router

# 独自のFastAPIインスタンスを作成
api_app = FastAPI(title="請求書構造化システム API")

# CORS設定
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_app.get("/")
async def root():
    """ルートパスへのアクセスをAPIドキュメントにリダイレクト"""
    return RedirectResponse(url="/docs")


api_app.include_router(document_router)
