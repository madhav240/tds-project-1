from .utils import (
    DAY_NAMES, normalize_weekday, file_rename, collect_markdown_titles,
    validate_file_path, encode_image, cosine_similarity
)
from app import DATA_DIR
from app.ai_calls import get_chat_completions, get_embeddings
from fastapi import HTTPException
from dateutil import parser
from bs4 import BeautifulSoup
from PIL import Image
import speech_recognition as sr
import os
import subprocess
import requests
import sqlite3
import duckdb
import markdown2
import json

def generate_data(email):
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py",
                f"--root={DATA_DIR}",
                email,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return {
                "message": f"Data generated by {email} (Email ID)",
                "status": "success",
            }    
        else:
            raise ValueError(f"Data initialization failed with return code {result.returncode}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_file(source: str = None) -> dict:
    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        result = subprocess.run(
            ["npx", "prettier@3.4.2", "--write", file_path],
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )

        if result.stderr:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {"message": "File formatted", "source": file_path, "status": "success"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=str(e))

def count_weekday(weekday: str, source: str = None, destination: str = None) -> dict:
    weekday = normalize_weekday(weekday)
    weekday_index = DAY_NAMES.index(weekday)

    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source
    output_path: str = destination or file_rename(file_path, f"-{weekday}.txt")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r") as f:
        dates = [parser.parse(line.strip()) for line in f if line.strip()]

    day_count = sum(1 for d in dates if d.weekday() == weekday_index)

    with open(output_path, "w") as f:
        f.write(str(day_count))

    return {
        "message": f"{weekday} counted",
        "count": day_count,
        "source": file_path,
        "destination": output_path,
        "status": "success",
    }


def sort_contacts(
    order: str = None, source: str = None, destination: str = None
) -> dict:
    order = order or "last_name"

    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source
    output_path: str = destination or file_rename(file_path, "-sorted.json")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r") as f:
        contacts = json.load(f)

    key1: str = "last_name" if order != "first_name" else "first_name"
    key2: str = "last_name" if key1 == "first_name" else "first_name"

    contacts.sort(key=lambda x: (x.get(key1, ""), x.get(key2, "")))

    with open(output_path, "w") as f:
        json.dump(contacts, f, indent=4)

    return {
        "message": "Contacts sorted",
        "source": file_path,
        "destination": output_path,
        "status": "success",
    }


def write_recent_logs(count: int, source: str = None, destination: str = None):
    if count < 1:
        raise HTTPException(status_code=400, detail="Invalid count")

    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source
    file_dir: str = os.path.dirname(file_path)
    output_path: str = destination or os.path.join(DATA_DIR, f"{file_dir}-recent.txt")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    log_files = sorted(
        [
            os.path.join(file_path, f)
            for f in os.listdir(file_path)
            if f.endswith(".log")
        ],
        key=os.path.getmtime,
        reverse=True,
    )

    with open(output_path, "w") as out:
        for log_file in log_files[:count]:
            with open(log_file, "r") as f:
                first_line = f.readline().strip()
                out.write(f"{first_line}\n")

    return {
        "message": "Recent logs written",
        "log_dir": file_path,
        "destination": output_path,
        "status": "success",
    }

def extract_markdown_titles(source: str = None, destination: str = None):
    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source
    output_path: str = destination or os.path.join(file_path, "index.json")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    index = {}
    collect_markdown_titles(file_path, index)

    with open(output_path, "w") as f:
        json.dump(index, f, indent=4)

    return {
        "message": "Markdown titles extracted",
        "file_dir": file_path,
        "index_file": output_path,
        "status": "success",
    }

def extract_email_sender(source: str = None, destination: str = None):
    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source
    output_path: str = destination or file_rename(file_path, "-sender.txt")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r") as f:
        email_content = f.read()

    response = get_chat_completions(
        [
            {"role": "system", "content": "Extract the sender's email."},
            {"role": "user", "content": email_content},
        ]
    )

    extracted_email = response["content"].strip()

    with open(output_path, "w") as f:
        f.write(extracted_email)

    return {
        "message": "Email extracted",
        "source": file_path,
        "destination": output_path,
        "status": "success",
    }


def extract_credit_card_number(source: str = None, destination: str = None):
    if not source:
        raise HTTPException(status_code=400, detail="Source file is required")

    file_path: str = source
    output_path: str = destination or file_rename(file_path, "-number.txt")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    image_data = encode_image(source)

    messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "There is 8 or more digit number is there in this image, with space after every 4 digit, only extract the those digit number without spaces and return just the number without any other characters",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                    },
                ],
            }
        ]
    
    response = get_chat_completions(messages)
    extracted_number = response["content"].replace(" ", "")

    with open(output_path, "w") as f:
        f.write(extracted_number)

    return {
        "message": "Credit card number extracted",
        "source": file_path,
        "destination": output_path,
        "status": "success",
    }


def find_similar_comments(source: str = None, destination: str = None):
    if not source:
        raise ValueError("Source file is required")

    file_path = source
    output_path = destination or file_rename(file_path, "-similar.txt")

    if not os.path.exists(file_path):
        raise FileNotFoundError("File not found")

    with open(file_path, "r", encoding="utf-8") as f:
        comments = [line.strip() for line in f.readlines()]

    embeddings = [get_embeddings(comment) for comment in comments]

    most_similar_pair = max(
        (
            (
                comments[i],
                comments[j],
                cosine_similarity(embeddings[i], embeddings[j]),
            )
            for i in range(len(comments))
            for j in range(i + 1, len(comments))
        ),
        key=lambda x: x[2],
        default=(None, None, -1),
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(most_similar_pair[:2]))

    return {
        "message": "Similar comments extracted",
        "source": file_path,
        "destination": output_path,
        "status": "success",
    }



def calculate_ticket_sales(database, ticket_type, destination):
    db_path = os.path.join(DATA_DIR, database)
    output_path = os.path.join(DATA_DIR, destination)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT SUM(units * price) FROM tickets WHERE type = '{ticket_type}'")
    total_sales = cursor.fetchone()[0] or 0

    conn.close()

    with open(output_path, "w") as f:
        f.write(str(total_sales))

    return {
        "message": "Sales calculated",
        "total_sales": total_sales,
        "status": "success",
    }

def fetch_api_data(url, destination = None):
    """Fetch JSON data from an API and save it."""
    response = requests.get(url)
    if response.status_code == 200:
        if destination:
            with open(destination, "w") as f:
                f.write(response.text)

            message = f"API data saved to {destination}",

        else:
            message = f"API data:\n\n{response.text}",
    else:
        raise HTTPException(status_code=500, detail="API request failed")
    
    return {
        "message": message,
        "source": url,
        "destination": destination,
        "status": "success"
    }

def git_operation(repo_url, operation, message=None, file_to_edit=None, new_content=None):
    """Clones a git repo, optionally modifies a file, and commits the change."""
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    subprocess.run(["git", "clone", repo_url, f"/data/{repo_name}"])
    
    if operation == "commit":
        if message and file_to_edit and new_content:
            validate_file_path(f"/data/{repo_name}/{file_to_edit}")  # Security check
            with open(f"/data/{repo_name}/{file_to_edit}", "w") as f:
                f.write(new_content)
            subprocess.run(["git", "add", file_to_edit], cwd=f"/data/{repo_name}")
            subprocess.run(["git", "commit", "-m", message], cwd=f"/data/{repo_name}")
        else:
            raise ValueError("Missing parameters! Check: commit message, file to edit and new content.")
        
        message = f"Repo {repo_name} cloned and modified.",

    message = f"Repo {repo_name} cloned.",

    return {
        "message": message,
        "source": repo_url,
        "operation": operation,
        "status": "success"
    }

def run_sql_query(db_type, db_file, query, destination=None):
    """Executes a SQL query on SQLite or DuckDB and saves the results."""
    validate_file_path(db_file)
    
    if db_type == "sqlite":
        conn = sqlite3.connect(db_file)
    elif db_type == "duckdb":
        conn = duckdb.connect(db_file)
    else:
        return "Unsupported database type."

    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    with open(destination, "w") as f:
        json.dump(results, f)

    conn.close()

    return {
        "message": f"SQL query executed and saved to {destination}",
        "status": "success"
    }

def scrape_website(url, destination=None):
    """Scrapes a website and extracts text content."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text_content = soup.get_text()

    if destination:
        with open(destination, "w") as f:
            f.write(text_content)

        message = f"Website data saved.",

    message = f"Below is the text content of the website:\n\n{text_content}",

    return {
        "message": message,
        "source": url,
        "destination": destination,
        "status": "success"
    }
    
def process_image(source: str, destination: str, action: str, width: int = None, height: int = None):
    validate_file_path(source)
    img = Image.open(source)
    
    if action == "compress":
        img.save(destination, optimize=True, quality=50)
    elif action == "resize" and width and height:
        img = img.resize((width, height))
        img.save(destination)
    else:
        raise ValueError("Invalid action or missing dimensions.")
    
    return {
        "message": "Image processed successfully.",
        "source": source,
        "destination": destination,
        "action": action,
        "status": "success"
    }

def transcribe_audio(source: str, destination: str, language: str = "en"):
    recognizer = sr.Recognizer()
    with sr.AudioFile(source) as source_audio:
        audio_data = recognizer.record(source_audio)
        text = recognizer.recognize_google(audio_data, language=language)

    if destination:
        with open(destination, "w") as file:
            file.write(text)

        message = f"Transcription saved to {destination}",

    message = f"Below is the transcription:\n\n{text}",

    return {
        "message": message,
        "source": source,
        "destination": destination,
        "language": language,
        "status": "success"
    }

def convert_markdown_to_html(source, destination=None):
    """Converts a Markdown file to HTML."""
    validate_file_path(source)
    with open(source, "r") as f:
        md_content = f.read()

    html_content = markdown2.markdown(md_content)

    if destination:
        with open(destination, "w") as f:
            f.write(html_content)
        
        message = f"Markdown converted to HTML."
    
    message = html_content

    return {
        "message": message,
        "source": source,
        "destination": destination,
        "status": "success"
    }
