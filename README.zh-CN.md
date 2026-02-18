# Ansible Galaxy Docker Compose

[![CI](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/ci.yml/badge.svg)](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/ci.yml)
[![Release](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/release.yml/badge.svg)](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/release.yml)
[![Scale Test](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/scale-test.yml/badge.svg)](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/scale-test.yml)

**📚 文档: [https://andrewdi.github.io/ansible-galaxy-compose/](https://andrewdi.github.io/ansible-galaxy-compose/)**

---

基于 [galaxy-operator](https://github.com/ansible/galaxy-operator) 的原生 Docker Compose 配置。

## 组件

本项目包含以下核心组件：

- **PostgreSQL 15** - 主数据库存储 Galaxy 数据
- **Redis 7** - 缓存和消息队列
- **Galaxy API** - Pulp 3 Galaxy API 服务
- **Galaxy Content** - 内容服务组件
- **Galaxy Worker** - 后台任务工作节点
- **Galaxy Web UI** - Web 用户界面

> **注意**: 未包含 Nginx，Galaxy 服务直接暴露端口访问

## 镜像来源

本配置使用 quay.io 提供的预构建镜像：

```yaml
# docker-compose.yml 中的镜像配置
galaxy-api:
  image: quay.io/ansible/galaxy-ng:latest

galaxy-web:
  image: quay.io/ansible/galaxy-ui:latest
```

## 快速开始

### 1. 环境准备

```bash
# 复制环境变量文件
cp .env.example .env

# 创建证书目录
mkdir -p certs

# 生成数据库加密密钥（pulpcore必需）
# 首次运行时会自动生成，也可手动生成：
python3 -c "import os; print(os.urandom(32).hex())" > certs/database_fields.symmetric.key
chmod 600 certs/database_fields.symmetric.key

# 编辑环境变量（可选）
vim .env
```

### 2. 启动服务

```bash
# 创建网络和卷
docker compose up -d

# 查看日志
docker compose logs -f
```

### 3. 访问服务

- **Web UI**: http://localhost:8080
- **API**: http://localhost:8000/api/galaxy/
- **Pulp API**: http://localhost:8000/pulp/api/v3/
- **Content**: http://localhost:24816/pulp/content/

默认管理员账户：
- 用户名: `admin`
- 密码: `admin`

### 4. 停止服务

```bash
docker compose down

# 保留数据
docker compose down -v

# 完全清理（包括卷）
docker compose down -v --remove-orphans
```

## 配置说明

### 环境变量

主要配置项：

| 变量 | 默认值 | 描述 |
|------|---------|------|
| `POSTGRESQL_USER` | galaxy | 数据库用户名 |
| `POSTGRESQL_PASSWORD` | galaxy | 数据库密码 |
| `POSTGRESQL_HOST` | postgres | 数据库主机 |
| `POSTGRESQL_PORT` | 5432 | 数据库端口 |
| `REDIS_HOST` | redis | Redis 主机 |
| `REDIS_PORT` | 6379 | Redis 端口 |
| `REDIS_PASSWORD` | galaxy | Redis 密码 |
| `GALAXY_ADMIN_USER` | admin | 管理员用户名 |
| `GALAXY_ADMIN_PASSWORD` | admin | 管理员密码 |
| `PULP_SECRET_KEY` | - | Django 密钥 |
| `GALAXY_API_HOSTNAME` | http://galaxy-web.orb.local | Galaxy API 地址 |

### 自定义镜像版本

在 `docker-compose.yml` 中修改镜像版本：

```yaml
services:
  galaxy-api:
    image: quay.io/ansible/galaxy-ng:v1.0.0
```

### 持久化存储

数据保存在以下 Docker 卷中：

- `postgres_data` - PostgreSQL 数据
- `galaxy_api_data` - Galaxy API、Content 和 Worker 共享数据（制品等）

> **注意**: Redis 配置为非持久化模式，数据不会持久化保存

## 开发与调试

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs galaxy-api

# 实时日志
docker compose logs -f galaxy-api
```

### 进入容器

```bash
# 进入 API 容器
docker exec -it galaxy-api bash

# 进入数据库容器
docker exec -it galaxy-postgres psql -U galaxy
```

### 执行管理命令

```bash
# 进入 API 容器
docker exec -it galaxy-api bash

# 运行 Django 管理命令
python manage.py createsuperuser
python manage.py collectstatic
```

## 生产部署建议

1. **修改默认密码**: 更新 `.env` 文件中的所有密码
2. **使用外部数据库**: 将 PostgreSQL 配置为外部托管数据库
3. **添加反向代理**: 可选添加 Nginx 或其他代理实现 HTTPS 和负载均衡
4. **资源限制**: 在 `docker-compose.yml` 中添加资源限制
5. **备份策略**: 定期备份 `postgres_data` 卷

## 项目结构

```
ansible-galaxy/
├── docker-compose.yml          # 主配置文件
├── .env.example               # 环境变量示例
├── .env.ci                   # CI环境变量
├── .gitignore                 # Git 忽略文件
├── README.md                  # 英文版本
├── README.zh-CN.md            # 本文档
├── LICENSE                    # 木兰PSL v2许可证
├── Makefile                   # 便利命令
├── ansible.cfg                # Ansible配置
├── certs/                     # SSL/TLS证书
├── config/
│   └── settings.py            # Galaxy/Pulp 配置
├── galaxy_service/            # Galaxy测试集合
│   ├── GALAXY.yml
│   ├── README.md
│   └── plugins/
├── init-scripts/
│   └── 01-init-db.sh         # 数据库初始化脚本
├── nginx/                     # Nginx配置
│   ├── nginx.conf
│   └── conf.d/
└── scripts/                   # 备份和工具脚本
    ├── backup.sh
    ├── restore.sh
    └── scheduler.sh
```

## 故障排除

### PostgreSQL 连接失败

```bash
# 检查 PostgreSQL 状态
docker compose logs postgres

# 重启 PostgreSQL
docker compose restart postgres
```

### Galaxy API 启动失败

```bash
# 检查 API 日志
docker compose logs galaxy-api

# 确保数据库已完全启动
docker compose ps
```

### 端口冲突

如果以下端口被占用，可以修改 `docker-compose.yml` 中的端口映射：

| 服务 | 默认端口 | 说明 |
|------|----------|------|
| Galaxy Web | 8080 | Web UI 端口 |
| Galaxy API | 8000 | API 服务端口 |
| Galaxy Content | 24816 | Content 服务端口 |
| PostgreSQL | 5432 | 数据库端口 |
| Redis | 6379 | 缓存端口 |

修改示例：

```yaml
galaxy-web:
  ports:
    - "8081:8080"  # 改为 8081 端口
```

## 相关链接

- [📚 文档](https://andrewdi.github.io/ansible-galaxy-compose/) - 完整配置参考文档
- [Galaxy Operator 文档](https://galaxy-operator.readthedocs.io/)
- [Pulp Project](https://pulpproject.org/)
- [Ansible Galaxy](https://galaxy.ansible.com/)
