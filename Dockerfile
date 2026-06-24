# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global --add safe.directory '*'

WORKDIR /app
COPY backend/ ./backend/
COPY --from=frontend /app/frontend/dist ./backend/commit_reviewer/web/
RUN pip install --no-cache-dir ./backend

ENV COMMIT_REVIEWER_HOST=0.0.0.0
EXPOSE 3546

ENTRYPOINT ["review-commits"]
