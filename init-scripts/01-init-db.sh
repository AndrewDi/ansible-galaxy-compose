#!/bin/bash
set -e

echo "Initializing Galaxy database..."

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -h localhost; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done

echo "PostgreSQL is ready. Running database migrations..."

# Create initial admin user
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
-- Create superuser if not exists
INSERT INTO auth_user (username, password, email, is_staff, is_superuser, is_active, date_joined)
VALUES (
    'admin',
    'pbkdf2_sha256\$600000\$test\$test',
    'admin@example.com',
    true,
    true,
    true,
    NOW()
)
ON CONFLICT (username) DO NOTHING;

-- Create Galaxy settings
INSERT INTO galaxy_settings_galaxysettings (id, update_strategy, allow_local_content, deployment_notifications, signature_notifications)
VALUES (1, 'immediate', false, true, true)
ON CONFLICT (id) DO NOTHING;

-- Create default groups
INSERT INTO galaxy_groups_group (id, name, description)
VALUES 
    (1, 'system:partner-engineers', 'Partner engineers group'),
    (2, 'system:authenticated-users', 'All authenticated users')
ON CONFLICT DO NOTHING;

EOF

echo "Database initialization complete!"