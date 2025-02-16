import re
import json
import os
import base64
import numpy as np

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def validate_file_path(filepath):
    """Ensure the file path is inside /data/."""
    abs_path = os.path.abspath(filepath)
    if not abs_path.startswith("/data/"):
        raise ValueError(f"Access to {filepath} is not allowed. Only /data/ directory is permitted.")

def parse_function_args(function_args):
    if function_args is not None:
        if isinstance(function_args, str):
            function_args = json.loads(function_args)

        elif not isinstance(function_args, dict):
            function_args = {"args": function_args}
    else:
        function_args = {}

    return function_args

def file_rename(name: str, suffix: str) -> str:
    return (re.sub(r"\.(\w+)$", "", name) + suffix).lower()

def normalize_weekday(weekday):
    if isinstance(weekday, int):  # If input is an integer (0-6)
        return DAY_NAMES[weekday % 7]

    elif isinstance(weekday, str):  # If input is a string
        weekday = weekday.strip().lower()
        days = {day.lower(): day for day in DAY_NAMES}
        short_days = {day[:3].lower(): day for day in DAY_NAMES}

        if weekday in days:
            return days[weekday]

        elif weekday in short_days:
            return short_days[weekday]

    raise ValueError("Invalid weekday input")

def collect_markdown_titles(directory: str, index: dict):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    title = None
                    for line in f:
                        if line.strip().startswith("#"):
                            title = line.strip().lstrip("#").strip()
                            break

                    if title:
                        relative_path = os.path.relpath(file_path, directory)
                        relative_path = re.sub(r"[\\/]+", "/", relative_path)
                        index[relative_path] = title

# Read the image file and encode it as base64
def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")
    
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))