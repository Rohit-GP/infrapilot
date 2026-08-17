from fastapi import FastAPI


app = FastAPI(
    title="InfraPilot API",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "InfraPilot API",
    }