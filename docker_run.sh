#!/bin/bash
# Docker execution script for Anastasia IEDB Pipeline
# Mounts external data directory and runs the pipeline
#
# Usage:
#   ./docker_run.sh [DATA_DIR] [OUTPUT_DIR]
#   or
#   DATA_DIR=/path/to/data OUTPUT_DIR=/path/to/output ./docker_run.sh
#
# author: Michael W. Gaunt, Ph.D

set -e

# Default values
DATA_DIR="${1:-${DATA_DIR:-./data}}"
OUTPUT_DIR="${2:-${OUTPUT_DIR:-./output}}"
IMAGE_NAME="${IMAGE_NAME:-anastasia:latest}"

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory '$DATA_DIR' does not exist"
    echo ""
    echo "Usage:"
    echo "  ./docker_run.sh [DATA_DIR] [OUTPUT_DIR]"
    echo "  or"
    echo "  DATA_DIR=/path/to/data OUTPUT_DIR=/path/to/output ./docker_run.sh"
    echo ""
    echo "The data directory must contain exactly 2 CSV files:"
    echo "  - One file with 'ref' in the filename (reference data)"
    echo "  - One file without 'ref' (query data)"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Convert to absolute paths
DATA_DIR=$(realpath "$DATA_DIR")
OUTPUT_DIR=$(realpath "$OUTPUT_DIR")

echo "=========================================="
echo "Anastasia IEDB Pipeline Execution"
echo "=========================================="
echo "Data directory: $DATA_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Docker image: $IMAGE_NAME"
echo ""

# Check for CSV files
CSV_COUNT=$(find "$DATA_DIR" -maxdepth 1 -name "*.csv" 2>/dev/null | wc -l)
if [ "$CSV_COUNT" -ne 2 ]; then
    echo "Warning: Data directory contains $CSV_COUNT CSV file(s), expected 2"
fi

# Prepare environment variables
ENV_ARGS=(-e BASE_DIR=/app -e OUTPUT_ROOT=/app/outputs)

# If REF_CSV and QUERY_CSV are explicitly set, pass them to container
# (Files must be within DATA_DIR or their paths will be passed as absolute paths)
if [ -n "$REF_CSV" ] && [ -n "$QUERY_CSV" ]; then
    # Check if files are relative to DATA_DIR or absolute
    if [[ "$REF_CSV" != /* ]]; then
        REF_CSV="$DATA_DIR/$REF_CSV"
    fi
    if [[ "$QUERY_CSV" != /* ]]; then
        QUERY_CSV="$DATA_DIR/$QUERY_CSV"
    fi
    REF_CSV_ABS=$(realpath "$REF_CSV")
    QUERY_CSV_ABS=$(realpath "$QUERY_CSV")
    ENV_ARGS+=(-e "REF_CSV=$REF_CSV_ABS" -e "QUERY_CSV=$QUERY_CSV_ABS")
    echo "Using explicit CSV files:"
    echo "  Reference: $REF_CSV_ABS"
    echo "  Query: $QUERY_CSV_ABS"
fi

# Run Docker container with volume mounts
docker run --rm \
    -v "${DATA_DIR}:/app/data:ro" \
    -v "${OUTPUT_DIR}:/app/outputs" \
    "${ENV_ARGS[@]}" \
    "$IMAGE_NAME"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✓ Pipeline completed successfully!"
    echo "Check output in: $OUTPUT_DIR"
else
    echo ""
    echo "✗ Pipeline failed with exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi

