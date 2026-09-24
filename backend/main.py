from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from routes.users import router as users_router
from routes.auth import router as auth_router
from routes.chat import router as chat_router

app = FastAPI(
    title="MarketingOS AI",
    description="Agentic AI-powered digital marketing workspace",
    version="1.0.0",
)


app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(users_router)

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


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "MarketingOS AI Backend",
    }