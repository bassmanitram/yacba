#!/bin/bash
# Simple backup script for yacba project

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/$TIMESTAMP"

echo "Creating backup in: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Copy all important files and directories
cp -r code sample-tool-configs sample-python-tools sample-model-configs README.md LICENSE "$BACKUP_DIR/"

echo "Backup completed successfully!"
echo "Files backed up to: $BACKUP_DIR"
ls -la "$BACKUP_DIR"
