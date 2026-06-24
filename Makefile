.PHONY: dev down logs build

dev:
    docker compose -f docker/docker-compose.dev.yml up --build

down:
    docker compose -f docker/docker-compose.dev.yml down

logs:
    docker compose -f docker/docker-compose.dev.yml logs -f

build:
    docker compose -f docker/docker-compose.dev.yml build
