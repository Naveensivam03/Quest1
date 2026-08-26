#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
OCR_VENV="$ROOT_DIR/.venv-ocr"

echo "======================================"
echo " Quest1 Setup (macOS)"
echo "======================================"

# --------------------------------------------------
# Prerequisites
# --------------------------------------------------

echo
echo "Checking prerequisites..."

for command in uv ffmpeg psql pg_isready; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "ERROR: '$command' is required but was not found."
    echo "Install via Homebrew: brew install uv ffmpeg postgresql@16"
    exit 1
  fi

  echo "✓ $command"
done

# --------------------------------------------------
# Python
# --------------------------------------------------

echo
if command -v python3.14 >/dev/null 2>&1; then
  echo "✓ Python 3.14"
elif command -v python3 >/dev/null 2>&1; then
  echo "✓ Python (managed by uv)"
else
  echo "✓ Python will be managed by uv"
fi

# --------------------------------------------------
# PostgreSQL configuration
# --------------------------------------------------

echo
echo "PostgreSQL configuration"

read -r -p "PostgreSQL host [localhost]: " POSTGRES_HOST
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"

read -r -p "PostgreSQL port [5432]: " POSTGRES_PORT
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

read -r -p "PostgreSQL username [postgres]: " POSTGRES_USER
POSTGRES_USER="${POSTGRES_USER:-postgres}"

read -r -s -p "PostgreSQL password: " POSTGRES_PASSWORD
echo

if [ -z "$POSTGRES_PASSWORD" ]; then
  echo "ERROR: PostgreSQL password cannot be empty."
  exit 1
fi

DATABASE_NAME="quest1"

# --------------------------------------------------
# PostgreSQL
# --------------------------------------------------

echo
echo "Checking PostgreSQL..."

if ! PGPASSWORD="$POSTGRES_PASSWORD" pg_isready \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" >/dev/null 2>&1; then

  echo "ERROR: Could not connect to PostgreSQL."
  echo
  echo "Check:"
  echo "  Host:     $POSTGRES_HOST"
  echo "  Port:     $POSTGRES_PORT"
  echo "  Username: $POSTGRES_USER"
  exit 1
fi

echo "✓ PostgreSQL is running"

# --------------------------------------------------
# Database
# --------------------------------------------------

echo
echo "Checking Quest1 database..."

DB_EXISTS=$(
  PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d postgres \
    -tAc "SELECT 1 FROM pg_database WHERE datname='$DATABASE_NAME';"
)

if [ "$DB_EXISTS" != "1" ]; then
  echo "Creating database '$DATABASE_NAME'..."

  PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d postgres \
    -c "CREATE DATABASE $DATABASE_NAME;"

  echo "✓ Database created"
else
  echo "✓ Database '$DATABASE_NAME' already exists"
fi

# --------------------------------------------------
# Main Python environment
# --------------------------------------------------

echo
echo "Setting up main Python environment..."

cd "$BACKEND_DIR"

uv sync

echo "✓ Main environment ready"

# --------------------------------------------------
# OCR Python environment
# --------------------------------------------------

echo
echo "Setting up OCR environment..."

if [ ! -d "$OCR_VENV" ]; then
  cd "$ROOT_DIR"

  uv venv "$OCR_VENV" --python 3.13

  cd "$BACKEND_DIR"
else
  echo "✓ OCR virtual environment already exists"
fi

echo
echo "Installing PaddleOCR dependencies (macOS CPU edition)..."

uv pip install \
  --python "$OCR_VENV/bin/python" \
  "paddlepaddle" \
  "paddleocr==3.7.0" \
  "opencv-contrib-python==4.10.0.84"

echo "✓ OCR environment ready"

# --------------------------------------------------
# Environment configuration
# --------------------------------------------------

echo
echo "Configuring environment..."

DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$DATABASE_NAME"

cat >"$BACKEND_DIR/.env" <<EOF
DATABASE_URL=$DATABASE_URL
EOF

echo "✓ backend/.env configured"

# --------------------------------------------------
# Database migrations
# --------------------------------------------------

echo
echo "Running database migrations..."

DATABASE_URL="${DATABASE_URL/postgresql:\/\//postgresql+psycopg:\/\/}"

# Python string replacement safe for macOS BSD sed
uv run python -c "import sys; p='$BACKEND_DIR/alembic.ini'; lines=[f'sqlalchemy.url = $DATABASE_URL\n' if l.startswith('sqlalchemy.url =') else l for l in open(p)]; open(p,'w').writelines(lines)"

uv run alembic upgrade head

echo "✓ Database migrations complete"

# --------------------------------------------------
# Done
# --------------------------------------------------

echo
echo "======================================"
echo " Setup complete (macOS)"
echo "======================================"
echo
echo "Start Quest1 with:"
echo
echo "    ./run_mac.sh"
echo
