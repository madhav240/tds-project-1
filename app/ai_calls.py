from fastapi import HTTPException
import json
import httpx
import os

AI_TOKEN = os.getenv("AIPROXY_TOKEN")
AI_URL = "https://aiproxy.sanand.workers.dev/openai/v1"
AI_MODEL = "gpt-4o-mini"
AI_EMBEDDINGS_MODEL = "text-embedding-3-small"

with open("./tools.json", "r") as file:
    tools = json.load(file)

def get_task_tool(task_description):
    response = httpx.post(
        url=f"{AI_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {AI_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": AI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": task_description,
                }
            ],
            "tools": tools,
            "tool_choice": "auto"
        }
    )
    json_response = response.json()

    if "error" in json_response:
        raise HTTPException(500, json_response["error"]["message"])
    
    return json_response["choices"][0]["message"]

def get_chat_completions(messages):
    response = httpx.post(
        f"{AI_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {AI_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": AI_MODEL,
            "messages": messages,
        },
    )

    json_response = response.json()

    if "error" in json_response:
        raise HTTPException(status_code=500, detail=json_response["error"]["message"])

    return json_response["choices"][0]["message"]

def get_embeddings(text):
    response = httpx.post(
        f"{AI_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {AI_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "model": AI_EMBEDDINGS_MODEL,
            "input": text,
        },
    )

    json_response = response.json()

    if "error" in json_response:
        raise HTTPException(status_code=500, detail=json_response["error"]["message"])

    return json_response["data"][0]["embedding"]