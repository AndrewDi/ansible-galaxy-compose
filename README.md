# Ansible Galaxy Docker Compose

[![CI](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/ci.yml/badge.svg)](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/ci.yml)
[![Release](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/release.yml/badge.svg)](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/release.yml)
[![Scale Test](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/scale-test.yml/badge.svg)](https://github.com/AndrewDi/ansible-galaxy-compose/actions/workflows/scale-test.yml)

**📚 Documentation: [https://andrewdi.github.io/ansible-galaxy-compose/](https://andrewdi.github.io/ansible-galaxy-compose/)**

---

Native Docker Compose configuration based on [galaxy-operator](https://github.com/ansible/galaxy-operator).

## Components

This project includes the following core components:

- **PostgreSQL 15** - Primary database for Galaxy data
- **Redis 7** - Cache and message queue
- **Galaxy API** - Pulp 3 Galaxy API service
- **Galaxy Content** - Content service component
- **Galaxy Worker** - Background task worker
- **Galaxy Web UI** - Web user interface

> **Note**: Nginx is not included, Galaxy services are directly exposed via ports

## Image Sources

This configuration uses pre-built images from quay.io:

```yaml
# Image configuration in docker-compose.yml
galaxy-api:
  image: quay.io/ansible/galaxy-ng:latest

galaxy-web:
  image: quay.io/ansible/galaxy-ui:latest
```

## Quick Start

### 1. Environment Setup

```bash
# Copy environment variable file
cp .env.example .env

# Create certificates directory
mkdir -p certs

# Generate database encryption key (required for pulpcore)
# The key is automatically generated on first run, or you can generate it manually:
python3 -c "import os; print(os.urandom(32).hex())" > certs/database_fields.symmetric.key
chmod 600 certs/database_fields.symmetric.key

# Edit environment variables (optional)
vim .env
```

### 2. Start Services

```bash
# Create network and volumes
docker compose up -d

# View logs
docker compose logs -f
```

### 3. Access Services

- **Web UI**: http://localhost:8080
- **API**: http://localhost:8000/api/galaxy/
- **Pulp API**: http://localhost:8000/pulp/api/v3/
- **Content**: http://localhost:24816/pulp/content/

Default admin account:
- Username: `admin`
- Password: `admin`

### 4. Stop Services

```bash
docker compose down

# Keep data
docker compose down -v

# Full cleanup (including volumes)
docker compose down -v --remove-orphans
```

## Configuration

### Environment Variables

Main configuration options:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRESQL_USER` | galaxy | Database username |
| `POSTGRESQL_PASSWORD` | galaxy | Database password |
| `POSTGRESQL_HOST` | postgres | Database host |
| `POSTGRESQL_PORT` | 5432 | Database port |
| `REDIS_HOST` | redis | Redis host |
| `REDIS_PORT` | 6379 | Redis port |
| `REDIS_PASSWORD` | galaxy | Redis password |
| `GALAXY_ADMIN_USER` | admin | Admin username |
| `GALAXY_ADMIN_PASSWORD` | admin | Admin password |
| `PULP_SECRET_KEY` | - | Django secret key |
| `GALAXY_API_HOSTNAME` | http://galaxy-web.orb.local | Galaxy API hostname |

### Custom Image Version

Modify image version in `docker-compose.yml`:

```yaml
services:
  galaxy-api:
    image: quay.io/ansible/galaxy-ng:v1.0.0
```

### Persistent Storage

Data is stored in the following Docker volumes:

- `postgres_data` - PostgreSQL data
- `galaxy_api_data` - Galaxy API, Content, and Worker shared data (artifacts, etc.)

> **Note**: Redis is configured in non-persistent mode, data will not be persisted

## Development and Debugging

### View Logs

```bash
# View all service logs
docker compose logs

# View specific service logs
docker compose logs galaxy-api

# Real-time logs
docker compose logs -f galaxy-api
```

### Enter Container

```bash
# Enter API container
docker exec -it galaxy-api bash

# Enter database container
docker exec -it galaxy-postgres psql -U galaxy
```

### Execute Management Commands

```bash
# Enter API container
docker exec -it galaxy-api bash

# Run Django management commands
python manage.py createsuperuser
python manage.py collectstatic
```

## Production Deployment Recommendations

1. **Change default passwords**: Update all passwords in `.env` file
2. **Use external database**: Configure PostgreSQL as externally managed
3. **Add reverse proxy**: Optionally add Nginx or other proxy for HTTPS and load balancing
4. **Resource limits**: Add resource limits in `docker-compose.yml`
5. **Backup strategy**: Regularly backup `postgres_data` volume

## Project Structure

```
ansible-galaxy/
├── docker-compose.yml          # Main configuration file
├── .env.example               # Environment variables example
├── .env.ci                    # CI environment variables
├── .gitignore                 # Git ignore file
├── README.md                  # This document
├── README.zh-CN.md            # Chinese version
├── LICENSE                    # Mulan PSL v2 License
├── Makefile                   # Convenience commands
├── ansible.cfg                # Ansible configuration
├── certs/                     # SSL/TLS certificates
├── config/
│   └── settings.py            # Galaxy/Pulp configuration
├── galaxy_service/            # Galaxy collection for testing
│   ├── GALAXY.yml
│   ├── README.md
│   └── plugins/
├── init-scripts/
│   └── 01-init-db.sh         # Database initialization script
├── nginx/                     # Nginx configuration
│   ├── nginx.conf
│   └── conf.d/
└── scripts/                   # Backup and utility scripts
    ├── backup.sh
    ├── restore.sh
    └── scheduler.sh
```

## Troubleshooting

### PostgreSQL Connection Failed

```bash
# Check PostgreSQL status
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Galaxy API Startup Failed

```bash
# Check API logs
docker compose logs galaxy-api

# Ensure database is fully started
docker compose ps
```

### Port Conflicts

If the following ports are occupied, modify the port mappings in `docker-compose.yml`:

| Service | Default Port | Description |
|---------|-------------|-------------|
| Galaxy Web | 8080 | Web UI port |
| Galaxy API | 8000 | API service port |
| Galaxy Content | 24816 | Content service port |
| PostgreSQL | 5432 | Database port |
| Redis | 6379 | Cache port |

Example modification:

```yaml
galaxy-web:
  ports:
    - "8081:8080"  # Change to 8081
```

## Related Links

- [📚 Documentation](https://andrewdi.github.io/ansible-galaxy-compose/) - Full documentation with config reference
- [Galaxy Operator Documentation](https://galaxy-operator.readthedocs.io/)
- [Pulp Project](https://pulpproject.org/)
- [Ansible Galaxy](https://galaxy.ansible.com/)
