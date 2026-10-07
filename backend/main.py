# from fastapi import FastAPI, HTTPException
# from fastapi.responses import JSONResponse
# from backend.routes.users import router as users_router
# from backend.routes.auth import router as auth_router
# from backend.routes.chat import router as chat_router
# from backend.routes.knowledge import router as knowledge_router
# from backend.routes.brand_profile import router as brand_profile_router


# app = FastAPI(
#     title="MarketingOS AI",
#     description="Agentic AI-powered digital marketing workspace",
#     version="1.0.0",
# )


# app.include_router(chat_router)
# app.include_router(auth_router)
# app.include_router(users_router)
# app.include_router(knowledge_router)
# app.include_router(brand_profile_router)


# @app.exception_handler(HTTPException)
# async def http_exception_handler(
#     _request,
#     exc: HTTPException,
# ) -> JSONResponse:
#     if isinstance(exc.detail, dict) and "success" in exc.detail:
#         return JSONResponse(
#             status_code=exc.status_code,
#             content=exc.detail,
#         )

#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "success": False,
#             "data": None,
#             "message": str(exc.detail),
#         },
#     )


# @app.get("/health")
# def health_check():
#     return {
#         "status": "ok",
#         "service": "MarketingOS AI Backend",
#     }

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.users import router as users_router
from backend.routes.auth import router as auth_router
from backend.routes.chat import router as chat_router
from backend.routes.knowledge import router as knowledge_router
from backend.routes.brand_profile import router as brand_profile_router


app = FastAPI(
    title="MarketingOS AI",
    description="Agentic AI-powered digital marketing workspace",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------
# Frontend runs on Vite during development.
# Allow both localhost and 127.0.0.1 variants.
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(knowledge_router)
app.include_router(brand_profile_router)


# ---------------------------------------------------------
# HTTP Exception Handler
# ---------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(
    _request,
    exc: HTTPException,
) -> JSONResponse:
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": str(exc.detail),
        },
    )


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "MarketingOS AI Backend",
    }

