from fastapi import FastAPI

app = FastAPI(
    title="MarketingOS AI",
    description="Agentic AI-powered digital marketing workspace",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "MarketingOS AI Backend",
    }