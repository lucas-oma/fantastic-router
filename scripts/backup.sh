#!/bin/bash

# Fantastic Router - Backup Script

set -e

BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fantastic_router_$DATE.sql"

echo "💾 Creating backup: $BACKUP_FILE"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U fantastic_user fantastic_router > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

echo "✅ Backup created: $BACKUP_FILE.gz"

# Keep only last 7 backups
find $BACKUP_DIR -name "fantastic_router_*.sql.gz" -mtime +7 -delete

echo "🧹 Cleaned up backups older than 7 days"
