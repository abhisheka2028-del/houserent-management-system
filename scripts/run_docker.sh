#!/usr/bin/env bash
# ==============================================================================
# HouseRent - Module 3: Docker Automation Script (Linux/macOS)
# ==============================================================================

set -euo pipefail

IMAGE_NAME="${DOCKER_IMAGE:-houserent:v1.0}"
CONTAINER_NAME="houserent-app"
PORT="5000"

ACTION="${1:-run}"

case "${ACTION}" in
    build)
        echo "[+] Building Docker image: ${IMAGE_NAME}..."
        docker build -t "${IMAGE_NAME}" .
        echo "[+] Build complete."
        ;;

    run)
        echo "[+] Ensuring data directory exists for persistent SQLite..."
        mkdir -p ./data

        if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo "[!] Container ${CONTAINER_NAME} already exists. Removing older instance..."
            docker rm -f "${CONTAINER_NAME}"
        fi

        echo "[+] Starting container '${CONTAINER_NAME}' on http://localhost:${PORT}..."
        docker run -d \
            --name "${CONTAINER_NAME}" \
            -p "${PORT}:5000" \
            -v "$(pwd)/data:/app/data" \
            -e FLASK_ENV=production \
            -e SECRET_KEY="docker-run-secure-key-2026" \
            -e DATABASE_PATH="/app/data/houserent.db" \
            -e UPLOAD_FOLDER="/app/data/uploads" \
            "${IMAGE_NAME}"

        echo "[+] Container running! Waiting for health check..."
        sleep 4
        docker ps --filter "name=${CONTAINER_NAME}"
        echo ""
        echo "Access application at: http://localhost:${PORT}"
        ;;

    compose)
        echo "[+] Starting application via Docker Compose..."
        docker compose up -d --build
        docker compose ps
        ;;

    logs)
        docker logs -f "${CONTAINER_NAME}"
        ;;

    stop)
        echo "[*] Stopping container: ${CONTAINER_NAME}..."
        docker stop "${CONTAINER_NAME}"
        ;;

    clean)
        echo "[!] Removing container: ${CONTAINER_NAME}..."
        docker rm -f "${CONTAINER_NAME}" || true
        ;;

    tag-push)
        USER="${2:?Error: Docker Hub username required as 2nd argument}"
        echo "[+] Tagging image for Docker Hub: ${USER}/houserent:v1.0..."
        docker tag "${IMAGE_NAME}" "${USER}/houserent:v1.0"
        echo "[+] Pushing to Docker Hub..."
        docker push "${USER}/houserent:v1.0"
        ;;

    *)
        echo "Usage: $0 {build|run|compose|logs|stop|clean|tag-push <username>}"
        exit 1
        ;;
esac
