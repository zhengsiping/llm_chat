from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from cores.rag import audio_query
from server.routers import query
import os

from utils.constants import Region

# os.environ["Region"] = Region.US
# os.environ["Region"] = Region.CHINA

print("Region set to:", os.environ["Region"])
app = FastAPI()
# Define allowed origins
origins = [
    "http://localhost:5174",
    "https://localhost:5173",
    "https://localhost:5174",
    "http://localhost:3000",  # React/Vue/Angular development
    "http://118.178.91.36/",     # Allow specific domain
    "https://118.178.91.36/",     # Allow specific domain
    "*",  # Allow all origins (not recommended for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specified origins
    allow_credentials=True,  # Allow cookies/auth
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="./certs/key.pem",
        ssl_certfile="./certs/cert.pem"
    )

# Include the router
app.include_router(query.router)
app.include_router(audio_query.router)
