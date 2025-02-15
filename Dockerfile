FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY . .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run the datagen.py script with the specified argument
RUN uv run https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py 23f2001923@ds.study.iitm.ac.in

# Expose the port the app runs on
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]