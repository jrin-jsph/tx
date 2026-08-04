#!/usr/bin/env bash
# MUX Linux Installation Script
set -e

echo "Installing MUX on Linux..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .

echo "Checking installation..."
python3 -m mux status
