#!/bin/bash

set -euxo pipefail

echo "=========================="
echo "Deploy Start"
echo "=========================="

cd ~/projects/twse

echo "Fetch latest code..."
git fetch origin

echo "Reset to origin/main..."
git reset --hard origin/main

echo "Build and restart container..."
docker compose up -d --build --remove-orphans

echo "Web API check"
./health_check.sh

echo "Deploy Success"