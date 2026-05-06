import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import UPLOAD_FOLDER
from routes.todo import api_router
from routes.users import api_router as users_router


app = FastAPI()


@app.middleware("http")
async def log_request(request: Request, call_next):
    print(f"Request: {request.method} {request.url.path}")
    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()
    print(f"Response: {response.status_code}, Time taken: {end_time - start_time:.2f} seconds")
    response.headers["X-Process-Time"] = str(end_time - start_time)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(users_router)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_FOLDER), name="static")
