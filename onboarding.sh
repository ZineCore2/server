#!/usr/bin/env bash
set -e

echo "ZineCore2 Server Onboarding"
echo "==========================="
echo ""
uv run --group dev python onboarding.py
