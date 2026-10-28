# Stage 1: build the React frontend
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Flask serves the API and the built frontend
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY --from=web /web/dist frontend/dist
ENV WATTWISE_DB=/data/wattwise.db
RUN mkdir -p /data
WORKDIR /app/backend
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 1
