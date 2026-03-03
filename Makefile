.PHONY: help build up down restart logs clean test backup restore

# Default target
help:
	@echo "BRS-SASA Docker Management"
	@echo "=========================="
	@echo ""
	@echo "Development Commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services (development)"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs (all services)"
	@echo "  make logs-api       - View API logs"
	@echo "  make logs-ui        - View UI logs"
	@echo "  make logs-crm       - View CRM logs"
	@echo ""
	@echo "Production Commands:"
	@echo "  make prod-build     - Build production images"
	@echo "  make prod-up        - Start production services"
	@echo "  make prod-down      - Stop production services"
	@echo "  make prod-restart   - Restart production services"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  make clean          - Remove containers and images"
	@echo "  make clean-all      - Remove everything including volumes"
	@echo "  make backup         - Backup data volumes"
	@echo "  make restore        - Restore from backup"
	@echo "  make shell-api      - Open shell in API container"
	@echo "  make shell-ui       - Open shell in UI container"
	@echo "  make shell-crm      - Open shell in CRM container"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test           - Run tests in container"
	@echo "  make check-db       - Check database status"
	@echo "  make health         - Check service health"
	@echo ""

# Development
build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "Services started!"
	@echo "  User Interface: http://localhost:8501"
	@echo "  CRM Dashboard:  http://localhost:8502"
	@echo "  API Docs:       http://localhost:8000/docs"
	@echo ""

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-ui:
	docker-compose logs -f ui

logs-crm:
	docker-compose logs -f crm

# Production
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d
	@echo ""
	@echo "Production services started!"
	@echo "  User Interface: http://localhost:8501"
	@echo "  CRM Dashboard:  http://localhost:8502"
	@echo "  API Docs:       http://localhost:8000/docs"
	@echo ""

prod-down:
	docker-compose -f docker-compose.prod.yml down

prod-restart:
	docker-compose -f docker-compose.prod.yml restart

prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

# Maintenance
clean:
	docker-compose down --rmi all

clean-all:
	docker-compose down -v --rmi all
	@echo "WARNING: All data has been removed!"

backup:
	@mkdir -p backups
	@tar -czf backups/brs-sasa-backup-$$(date +%Y%m%d-%H%M%S).tar.gz data/ logs/ chroma_data/ 2>/dev/null || true
	@echo "Backup created in backups/"

restore:
	@echo "Available backups:"
	@ls -lh backups/*.tar.gz 2>/dev/null || echo "No backups found"
	@echo ""
	@echo "To restore, run: tar -xzf backups/BACKUP_FILE.tar.gz"

shell-api:
	docker-compose exec api bash

shell-ui:
	docker-compose exec ui bash

shell-crm:
	docker-compose exec crm bash

# Testing
test:
	docker-compose exec api pytest -v

check-db:
	docker-compose exec api python -c "\
	from core.database import SessionLocal; \
	from core.models import FeedbackModel, IssueReportModel, ConversationModel, MessageModel; \
	db = SessionLocal(); \
	print(f'Feedback: {db.query(FeedbackModel).count()}'); \
	print(f'Issues: {db.query(IssueReportModel).count()}'); \
	print(f'Conversations: {db.query(ConversationModel).count()}'); \
	print(f'Messages: {db.query(MessageModel).count()}'); \
	db.close()"

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/api/v1/health/ | python -m json.tool || echo "API: DOWN"
	@curl -s -o /dev/null -w "UI: %{http_code}\n" http://localhost:8501
	@curl -s -o /dev/null -w "CRM: %{http_code}\n" http://localhost:8502

# Quick commands
start: up
stop: down
rebuild: down build up
status:
	docker-compose ps
