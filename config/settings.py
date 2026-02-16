import os

# Django settings for Galaxy (Pulp) project.

DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = ['*']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRESQL_DATABASE', 'galaxy'),
        'USER': os.environ.get('POSTGRESQL_USER', 'galaxy'),
        'PASSWORD': os.environ.get('POSTGRESQL_PASSWORD', 'galaxy'),
        'HOST': os.environ.get('POSTGRESQL_HOST', 'postgres'),
        'PORT': os.environ.get('POSTGRESQL_PORT', 5432),
        'CONN_MAX_AGE': 0,
    }
}

# Redis configuration
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', 'galaxy')
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)

CACHE_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': CACHE_URL,
    }
}

# Secret key for Django
SECRET_KEY = os.environ.get('PULP_SECRET_KEY', 'default-secret-key-change-in-production')

# Galaxy specific settings
GALAXY_ADMIN_USER = os.environ.get('GALAXY_ADMIN_USER', 'admin')
GALAXY_ADMIN_PASSWORD = os.environ.get('GALAXY_ADMIN_PASSWORD', 'admin')

# Content signing settings
GALAXY_CONTENT_SIGNING_ENABLED = os.environ.get('GALAXY_CONTENT_SIGNING_ENABLED', 'False')
GALAXY_GNUPG_HOME = os.environ.get('GALAXY_GNUPG_HOME', '/var/lib/pulp/gnupg')
GALAXY_SIGNING_SCRIPTS = os.environ.get('GALAXY_SIGNING_SCRIPTS', '/var/lib/pulp/scripts')
GALAXY_REQUIRE_SIGNATURE_FOR_APPROVAL = os.environ.get('GALAXY_REQUIRE_SIGNATURE_FOR_APPROVAL', 'False').lower() == 'true'
GALAXY_SIGNATURE_UPLOAD_ENABLED = os.environ.get('GALAXY_SIGNATURE_UPLOAD_ENABLED', 'False').lower() == 'true'
GALAXY_AUTO_SIGN_COLLECTIONS = os.environ.get('GALAXY_AUTO_SIGN_COLLECTIONS', 'False').lower() == 'true'

# Storage settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'pulp': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

GALAXY_API_DEFAULT_DISTRIBUTION_BASE_PATH = os.environ.get('GALAXY_API_DEFAULT_DISTRIBUTION_BASE_PATH', 'published')
GALAXY_API_STAGING_DISTRIBUTION_BASE_PATH = os.environ.get('GALAXY_API_STAGING_DISTRIBUTION_BASE_PATH', 'staging')

ANSIBLE_API_HOSTNAME = os.environ.get('GALAXY_API_HOSTNAME', 'http://galaxy-web.orb.local')
X_PULP_CONTENT_HOST = os.environ.get('X_PULP_CONTENT_HOST', 'galaxy-content')
X_PULP_CONTENT_PORT = int(os.environ.get('X_PULP_CONTENT_PORT', 24816))

# Galaxy feature flags
GALAXY_FEATURE_FLAGS = {
    'display_repositories': True,
    'execution_environments': os.environ.get('EE_ENABLED', 'False').lower() == 'true',
    'ai_deny_index': os.environ.get('AI_DENY_INDEX', 'False').lower() == 'true',
}

GALAXY_ENABLE_ANONYMOUS_ACCESS = os.environ.get('GALAXY_ENABLE_ANONYMOUS_ACCESS', 'True').lower() == 'true'
GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_DOWNLOAD = os.environ.get('GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_DOWNLOAD', 'True').lower() == 'true'
GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_ACCESS = os.environ.get('GALAXY_ENABLE_UNAUTHENTICATED_COLLECTION_ACCESS', 'True').lower() == 'true'

GALAXY_REQUIRE_CONTENT_APPROVAL = os.environ.get('GALAXY_REQUIRE_CONTENT_APPROVAL', 'False').lower() == 'true'
GALAXY_API_PATH_PREFIX = os.environ.get('GALAXY_API_PATH_PREFIX', 'api/galaxy')
GALAXY_ENABLE_LEGACY_ROLES = os.environ.get('GALAXY_ENABLE_LEGACY_ROLES', 'True').lower() == 'true'
GALAXY_DYNAMIC_SETTINGS = os.environ.get('GALAXY_DYNAMIC_SETTINGS', 'True').lower() == 'true'
STATIC_URL = os.environ.get('STATIC_URL', '/static/')

# CSRF settings
GALAXY_HOST = os.environ.get('GALAXY_API_HOSTNAME', 'http://localhost').replace('http://', '').replace('https://', '')
CONTENT_ORIGIN = os.environ.get('CONTENT_ORIGIN', "https://{GALAXY_HOST}")
CSRF_TRUSTED_ORIGINS = [
    f"http://{GALAXY_HOST}",
    f"https://{GALAXY_HOST}"
]
