# Mis Finanzas

Proyecto sencillo para registrar ingresos y gastos. Tiene una API en FastAPI, autenticación con JWT y una interfaz web hecha con React.

## Opción rápida (sin Docker)

Necesitas Python 3.12+ y Node.js 20+.

### Backend

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

La API queda en <http://localhost:8000> y su documentación en <http://localhost:8000/docs>. Si no se configura nada más, usa una base SQLite local (`finance.db`).

### Frontend

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Abre <http://localhost:5173>. Puedes crear una cuenta y comenzar a agregar una billetera, categorías y movimientos.

## Con Docker

```bash
cp .env.example .env
docker compose up --build
```

La API queda en <http://localhost:8000>. Para usar el frontend con Docker, ejecútalo localmente con los comandos anteriores; así es más fácil para un proyecto de clase.

## Variables útiles

- `JWT_SECRET`: cambia la llave usada para firmar las sesiones.
- `DATABASE_URL`: permite usar otra base de datos. Por defecto se usa SQLite.
- `FRONTEND_URL`: origen permitido por CORS, por defecto `http://localhost:5173`.
