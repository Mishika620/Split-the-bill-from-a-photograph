from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router


BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI(
    title="Split the Bill From a Photograph",
    description="Extract, review, validate, and split restaurant bills.",
    version="1.0.0",
)


app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


app.include_router(router)


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(
        BASE_DIR / "app" / "templates" / "index.html"
    )