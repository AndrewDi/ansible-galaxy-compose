.PHONY: help up down start stop restart logs status clean

help: ## 显示帮助信息
	@echo "Ansible Galaxy Docker Compose - 便利命令"
	@echo ""
	@echo "可用命令:"
	@echo "  make up              - 启动所有服务"
	@echo "  make down            - 停止所有服务"
	@echo "  make start           - 启动已存在的服务"
	@echo "  make stop            - 停止所有服务"
	@echo "  make restart         - 重启所有服务"
	@echo "  make logs            - 查看日志"
	@echo "  make status          - 查看服务状态"
	@echo "  make clean           - 完全清理包括数据卷"
	@echo ""
	@echo "  make backup          - 执行备份"
	@echo "  make backup-list     - 查看可用备份"
	@echo "  make restore         - 恢复备份"
	@echo "  make scheduler-start - 启动自动备份调度"
	@echo "  make scheduler-stop  - 停止自动备份调度"
	@echo ""
	@echo "  make scale-worker    - 扩展 Worker 数量"
	@echo "  make help            - 显示此帮助信息"

up: ## 启动所有服务
	@echo "启动 Galaxy 服务..."
	docker compose up -d
	@echo ""
	@echo "服务已启动!"
	@echo "Web UI: http://localhost:8080"
	@echo "API: http://localhost:8000/pulp/api/v3/"
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

backup: ## 执行完整备份
	@echo "执行完整备份..."
	@./scripts/backup.sh

backup-list: ## 查看可用备份
	@echo "可用备份文件:"
	@ls -lh backups/galaxy_backup_*.tar.gz 2>/dev/null || echo "暂无备份"

restore: ## 恢复备份
	@echo "从备份文件恢复数据库..."
	@./scripts/restore.sh

scheduler-start: ## 启动自动备份调度
	@./scripts/scheduler.sh start

scheduler-stop: ## 停止自动备份调度
	@./scripts/scheduler.sh stop

scheduler-status: ## 查看备份调度状态
	@./scripts/scheduler.sh status

scale-worker: ## 扩展 Worker 数量 (使用: make scale-worker N=3)
	@echo "扩展 Worker 数量到 $(or $(N),2)..."
	docker compose up -d --scale galaxy-worker=$(or $(N),2)

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
	@curl -s http://localhost:8000/api/galaxy/pulp/api/v3/status/ | head -c 200 || echo "API 不可用"

dev-up: ## 开发模式启动
	docker compose up -d

dev-logs: ## 开发模式查看日志
	docker compose logs -f galaxy-api galaxy-content galaxy-worker galaxy-web
