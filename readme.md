# ServiceFlow

ServiceFlow — internal service request and ticketing backend API.
Production-style backend project built with FastAPI, PostgreSQL and Docker.

The system is designed for internal company usage: IT support, helpdesk,
HR requests and operational service flows. The project demonstrates a clean
backend architecture with role-based access, business logic, migrations
and containerized deployment.

## Purpose

ServiceFlow can be used as:
- Internal IT / HelpDesk system
- HR request management backend
- Operations service request API
- Backend core for Telegram bots or web dashboards

## Features

- Service request creation and management
- Request status workflow: NEW → IN_PROGRESS → DONE / CANCELED
- Role-based access model:
  - ADMIN — full access
  - AGENT — request processing
  - EMPLOYEE — create and view own requests
- API key based authentication
- Request audit logs
- UUID / public_id identifiers
- PostgreSQL database with Alembic migrations
- Docker and Docker Compose support
- Seed script for initial data setup
- Automated tests

## Technology stack

- Python 3
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Docker / Docker Compose
- Pytest

## Project structure

- app/routers — API endpoints
- app/schemas — Pydantic schemas
- app/models — SQLAlchemy models
- app/services — business logic layer
- app/core — configuration, security, dependencies
- alembic — database migrations
- tests — automated tests

## Installation and run (Docker)

Requirements:
- Docker
- Docker Compose

1. Clone the repository

   git clone https://github.com/RiobVO/ServiceFlow.git
   cd ServiceFlow

2. Create environment file

   copy .env.example .env

3. Start the application

   docker compose up --build

4. Apply migrations (if needed)

   docker compose exec backend alembic upgrade head

After startup:
- API available at: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

## Environment variables

Environment variables are stored in .env file (do not commit it).

Main variables:
- DATABASE_URL_POSTGRES — PostgreSQL connection string
- API_KEY — API access key
- ADMIN_BOOTSTRAP_KEY — initial admin creation key

See .env.example for reference.

## API usage example

Create a service request:

POST /requests
X-API-Key: EMPLOYEE_API_KEY

Request body:
{
  "title": "VPN is not working",
  "description": "Connection drops every 5 minutes"
}

Change request status:

PATCH /requests/{id}/status
X-API-Key: AGENT_API_KEY

Request body:
{
  "status": "IN_PROGRESS"
}

## Tests

Run tests inside container:

docker compose exec backend pytest

## Roadmap

- Unified error handling
- Database healthcheck endpoint
- API key hashing and reset endpoint
- Extended audit logging
- ERD and request flow diagrams
- Admin panel or Telegram bot integration

## Author

Elyor Yusupov  
GitHub: https://github.com/RiobVO
