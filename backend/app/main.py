from fastapi import FastAPI

app = FastAPI(title="DAN API")


@app.get("/health")
def health():
    return {"status": "ok"}

