.PHONY: help up down start stop restart logs status clean

help: ## 显示帮助信息
	@echo "Ansible Galaxy Docker Compose - 便利命令"
	@echo ""
	@echo "可用命令:"
	@echo "  make up        - 启动所有服务"
	@echo "  make down      - 停止所有服务"
	@echo "  make start     - 启动已存在的服务"
	@echo "  make stop      - 停止所有服务"
	@echo "  make restart   - 重启所有服务"
	@echo "  make logs      - 查看日志"
	@echo "  make status    - 查看服务状态"
	@echo "  make clean     - 完全清理包括数据卷"
	@echo "  make help      - 显示此帮助信息"

up: ## 启动所有服务
	@echo "启动 Galaxy 服务..."
	docker compose up -d
	@echo ""
	@echo "服务已启动!"
	@echo "Web UI: http://localhost:8002"
	@echo "API: http://localhost:24817/pulp/api/v3/"
	@echo "管理员账户: admin / admin"

down: ## 停止所有服务
	@echo "停止 Galaxy 服务..."
	docker compose down

start: ## 启动已存在的服务
	@echo "启动 Galaxy 服务..."
	docker compose start

stop: ## 停止所有服务
	@echo "停止 Galaxy 服务..."
	docker compose stop

restart: ## 重启所有服务
	@echo "重启 Galaxy 服务..."
	docker compose restart

logs: ## 查看日志
	@echo "查看 Galaxy 服务日志..."
	docker compose logs -f

logs-api: ## 查看 API 日志
	@echo "查看 Galaxy API 日志..."
	docker compose logs -f galaxy-api

logs-web: ## 查看 Web 日志
	@echo "查看 Galaxy Web 日志..."
	docker compose logs -f galaxy-web

logs-db: ## 查看数据库日志
	@echo "查看 PostgreSQL 日志..."
	docker compose logs -f postgres

logs-worker: ## 查看 Worker 日志
	@echo "查看 Galaxy Worker 日志..."
	docker compose logs -f galaxy-worker

status: ## 查看服务状态
	@echo "Galaxy 服务状态:"
	@docker compose ps
	@echo ""
	@echo "资源使用情况:"
	@docker stats --no-stream $$(docker compose ps -q)

clean: ## 完全清理包括数据卷
	@echo "清理所有服务和数据卷..."
	@read -p "此操作将删除所有数据! 确定继续? [y/N] " -n 1 -r
	@echo
	@if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose down -v --remove-orphans; \
		echo "清理完成!"; \
	else \
		echo "已取消"; \
	fi

shell-api: ## 进入 API 容器
	docker exec -it galaxy-api bash

shell-web: ## 进入 Web 容器
	docker exec -it galaxy-web bash

shell-db: ## 进入数据库容器
	docker exec -it galaxy-postgres psql -U galaxy

shell-worker: ## 进入 Worker 容器
	docker exec -it galaxy-worker bash

db-migrate: ## 运行数据库迁移
	docker exec galaxy-api python /usr/local/bin/pulpcore-manager migrate

collectstatic: ## 收集静态文件
	docker exec galaxy-api python /usr/local/bin/pulpcore-manager collectstatic --noinput

createsuperuser: ## 创建超级用户
	docker exec -it galaxy-api python /usr/local/bin/pulpcore-manager createsuperuser

backup: ## 备份数据库
	@echo "备份数据库到 ./backups/$(shell date +%Y%m%d_%H%M%S).sql..."
	@mkdir -p backups
	@docker exec galaxy-postgres pg_dump -U galaxy galaxy > backups/galaxy_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## 恢复数据库
	@echo "从备份文件恢复数据库..."
	@read -p "输入备份文件名: " BACKUP_FILE; \
	if [ -f "backups/$$BACKUP_FILE" ]; then \
		docker exec -i galaxy-postgres psql -U galaxy galaxy < backups/$$BACKUP_FILE; \
		echo "恢复完成!"; \
	else \
		echo "备份文件不存在!"; \
	fi

pull: ## 拉取最新镜像
	docker compose pull

rebuild: ## 重新构建并启动
	docker compose down
	docker compose pull
	docker compose up -d

health: ## 检查服务健康状态
	@echo "检查 Galaxy 服务健康状态..."
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "API 健康检查:"
	@curl -s http://localhost/pulp/api/v3/status/ | head -c 200 || echo "API 不可用"

# 开发命令
dev-up: ## 开发模式启动（不启动 nginx）
	docker compose up -d postgres redis galaxy-api galaxy-content galaxy-worker galaxy-web

dev-logs: ## 开发模式查看日志
	docker compose logs -f galaxy-api galaxy-content galaxy-worker galaxy-web