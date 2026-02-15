# Galaxy Service Collection

An Ansible Collection for validating and testing Ansible Galaxy service.

## Installation

```bash
# Install from local path
ansible-galaxy collection install /path/to/galaxy_service

# Build for distribution
ansible-galaxy collection build galaxy_service/

# Publish to Galaxy
ansible-galaxy collection publish galaxy_service/<version>.tar.gz
```

## Usage

### Validate Galaxy Service

```yaml
- name: Validate Galaxy service
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Check Galaxy service health
      galaxy_service.galaxy_service.galaxy_service:
        galaxy_url: "https://galaxy-web.orb.local"
        username: "admin"
        password: "admin"
        action: validate
      register: result

    - name: Display result
      debug:
        msg: "Database connected: {{ result.database_connected }}"
```

### Test Complete Workflow

```yaml
- name: Test Galaxy workflow
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Run Galaxy test
      galaxy_service.galaxy_service.galaxy_service:
        galaxy_url: "https://galaxy-web.orb.local"
        username: "admin"
        password: "admin"
        action: test
        validate_certs: no
      register: result
```

### Upload Collection

```yaml
- name: Upload collection
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Upload collection
      galaxy_service.galaxy_service.galaxy_service:
        galaxy_url: "https://galaxy-web.orb.local"
        username: "admin"
        password: "admin"
        action: upload
        src: "/path/to/my_collection.tar.gz"
        validate_certs: no
```

## Module: galaxy_service

### Options

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| galaxy_url | yes | str | The URL of the Galaxy server |
| username | yes | str | Username for authentication |
| password | yes | str | Password for authentication |
| action | yes | str | Action to perform: validate, upload, download, test |
| collection_name | no | str | Collection name in namespace.name format |
| collection_version | no | str | Collection version |
| src | no | path | Path to collection tarball for upload |
| dest | no | path | Path to save downloaded collection |
| validate_certs | no | bool | Validate SSL certificates (default: True) |
| wait_timeout | no | int | Timeout for import task (default: 120s) |

### Return Values

| Key | Type | Description |
|-----|------|-------------|
| api_status | int | HTTP status code from API |
| database_connected | bool | Database connection status |
| redis_connected | bool | Redis connection status |
| components | dict | Galaxy components and versions |
| collections_count | int | Number of collections in server |
| upload_result | dict | Upload result information |

## License

GPL-3.0-or-later
