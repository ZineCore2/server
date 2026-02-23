#!/usr/bin/env bash
set -e

echo "Starting ZineCore2 Development Server"
echo "======================================"
echo ""

# Load .env so Django and docker compose share the same config
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker compose is running
echo "Checking Docker services..."
if ! docker compose ps --status running 2>/dev/null | grep -q "db"; then
    echo "Starting Docker Compose..."
    docker compose up -d --wait
    echo -e "${GREEN}PostgreSQL started${NC}"
else
    echo -e "${GREEN}PostgreSQL already running${NC}"
fi

echo ""

# Ensure spec submodule is available
if [ ! -d "spec/vocabularies/canonical" ]; then
    echo -e "${YELLOW}Initializing spec submodule...${NC}"
    git submodule update --init spec
    echo -e "${GREEN}Spec submodule ready${NC}"
    echo ""
fi

# Run any pending migrations
echo "Checking for pending migrations..."
DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py migrate --check --no-input 2>/dev/null || {
    echo -e "${YELLOW}Running pending migrations...${NC}"
    DJANGO_SETTINGS_MODULE=zinecore.settings.development \
        .venv/bin/python backend/manage.py migrate
}
echo -e "${GREEN}Database is up to date${NC}"

echo ""
echo "Starting Django development server..."
echo ""
echo "Services available at:"
echo "  API:          http://localhost:8000/api/"
echo "  Admin:        http://localhost:8000/admin/"
echo "  Swagger docs: http://localhost:8000/api/docs/"
echo ""
echo "Press Ctrl+C to stop"
echo ""

DJANGO_SETTINGS_MODULE=zinecore.settings.development \
    .venv/bin/python backend/manage.py runserver 0.0.0.0:8000
