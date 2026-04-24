import time

from fastapi import FastAPI, Request
from api import api_router
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

@app.middleware("http")
async def log_request(request: Request, call_next):
    print(f"Requests: {request.method} {request.url}, {request.headers}")
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
