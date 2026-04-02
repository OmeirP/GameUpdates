FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /code   

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# If any system dependencies were needed, write them there

# better for docker caching apparently.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the backend code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

