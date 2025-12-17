# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import websocket as websocket_router
from app.routers import auth as auth_router
from app.routers import alerts as alerts_router
from app.routers import stock as stock_router
from app.routers import qstash_alert as qstash_router
from app.core.config import settings
from colorama import Fore, Style, init

init(autoreset=True)

app = FastAPI(title="Stock Alert System")

origins = [
    "https://stock-alert-ui-sable.vercel.app",
    "http://localhost:5173",
    "https://stock-alert-oggae2zqc-ajay-bibins-projects.vercel.app/",
]

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(alerts_router.router, prefix="/alerts", tags=["alerts"])
app.include_router(websocket_router.router, prefix="", tags=["websocket"])
app.include_router(stock_router.router, prefix="/stock", tags=["stock"])
app.include_router(qstash_router.router, prefix="/tasks", tags=["qstash_alert"])

@app.get("/")
async def root():
    print(Fore.GREEN + "API 'root' endpoint accessed")
    return {"status": "ok", "app": "stock-alert-system", "message": "Welcome to the Stock Alert System!"}
