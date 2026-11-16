#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker no está instalado o no está disponible en el PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker no está iniciado. Abre Docker Desktop o inicia el servicio."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Se creó .env usando la configuración de desarrollo."
fi

echo "Levantando PostgreSQL, API y React dentro de Docker..."
docker compose up --build -d

echo "Esperando a que la API responda..."
for attempt in {1..30}; do
  if curl -fsS http://localhost:8000/ >/dev/null 2>&1; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    echo "La API no respondió. Revisa los logs con: docker compose logs app db"
    exit 1
  fi
  sleep 2
done

echo
echo "Proyecto listo:"
echo "  Interfaz: http://localhost:5173"
echo "  API:      http://localhost:8000/docs"
echo
echo "Para ver los logs: docker compose logs -f"
echo "Para detener todo: docker compose down"
