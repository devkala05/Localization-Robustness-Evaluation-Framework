#!/usr/bin/env bash
set -euo pipefail

echo "Removing previous run results to enforce complete re-evaluation..."
sudo rm -rf results/scenarios/*
sudo rm -f results/pipeline_state.json

echo "Starting orchestrator for all algorithms and scenarios from pipeline.yaml..."
./scripts/run_pipeline.sh

echo "Evaluating all logs and generating complete ranking summary with Gemini AI!"
