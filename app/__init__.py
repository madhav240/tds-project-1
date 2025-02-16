from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

app = FastAPI()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

DATA_DIR: str = "/data"

DEV_EMAIL: str = "madhavmishra1124@gmail.com"

AI_TOKEN = os.getenv("AIPROXY_TOKEN")
AI_URL = "https://aiproxy.sanand.workers.dev/openai/v1"
AI_MODEL = "gpt-4o-mini"
AI_EMBEDDINGS_MODEL = "text-embedding-3-small"