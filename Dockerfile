FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY backend ./backend

RUN pip install --upgrade pip

RUN pip install \
    fastapi \
    "uvicorn[standard]" \
    python-dotenv \
    httpx \
    pydantic

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
