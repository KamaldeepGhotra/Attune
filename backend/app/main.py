from fastapi import FastAPI

app = FastAPI(title="Attune")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
