from fastapi import FastAPI
import os

app = FastAPI()

ROOT_DIR: str = app.root_path
DATA_DIR: str = f"{ROOT_DIR}/data"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DEV_EMAIL: str = "madhavmishra1124@gmail.com"