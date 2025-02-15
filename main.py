from fastapi import HTTPException, Response
from app.ai_calls import get_task_tool
from app.utils import parse_function_args, validate_file_path
from app import tools
from app import app
import pandas as pd
import os

def execute_tool_calls(tool):
    if "tool_calls" in tool:
        for tool_call in tool["tool_calls"]:
            function_name = tool_call["function"].get("name")
            function_args = tool_call["function"].get("arguments")

            # Ensure the function name is valid and callable
            if hasattr(tools, function_name) and callable(getattr(tools, function_name)):
                function_chosen = getattr(tools, function_name)
                function_args = parse_function_args(function_args)

                if isinstance(function_args, dict):
                    return function_chosen(**function_args)

    raise HTTPException(status_code=400, detail="Unknown task")


@app.post("/run")
def run_task(task):
    if not task:
        raise HTTPException(status_code=400, detail="Task description is required")

    try:
        tool = get_task_tool(task)
        return execute_tool_calls(tool)
    except Exception as e:
        detail: str = e.detail if hasattr(e, "detail") else str(e)
        raise HTTPException(status_code=500, detail=detail)
    
@app.get("/read")
def read_file(path):
    if not path:
        raise HTTPException(status_code=400, detail="File path is required")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(path, "r") as f:
            content = f.read()
        return Response(content=content, media_type="text/plain")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@app.get("/filter_csv")
def filter_csv_data(column: str, value: str):
    """Filters a CSV file by column and value, then returns JSON."""
    csv_file = "/data/data.csv"
    validate_file_path(csv_file)
    
    df = pd.read_csv(csv_file)
    filtered_df = df[df[column] == value]

    return filtered_df.to_dict(orient="records")