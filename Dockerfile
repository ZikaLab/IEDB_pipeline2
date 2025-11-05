# Dockerfile for Anastasia IEDB Pipeline
# Compatible with AWS ECR (standard Docker format)
# Base: Python 3.10 slim for smaller image size

FROM python:3.10-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    perl \
    tcsh \
    gawk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory (this becomes the base path)
ENV WORKDIR=/app
WORKDIR $WORKDIR

# Copy requirements and install Python dependencies
COPY 1_ng_tc1-0.1.2-beta/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy entire project structure
COPY . $WORKDIR/

# Set environment variables for path resolution
ENV BASE_DIR=$WORKDIR
ENV PYTHONPATH=$WORKDIR/1_ng_tc1-0.1.2-beta/src:$PYTHONPATH
ENV PERL5LIB=$WORKDIR/vendor/1_ng_tc1-0.1.2-beta:$PERL5LIB

# Create necessary directories (output dirs created at runtime, but ensure data exists)
RUN mkdir -p $WORKDIR/data

# Make Perl scripts executable
RUN chmod +x $WORKDIR/vendor/1_ng_tc1-0.1.2-beta/*.pl && \
    chmod +x $WORKDIR/1_ng_tc1-0.1.2-beta/src/tcell_mhci.py

# Default command (override with docker run or task definition)
CMD ["python3", "iedb_run-cmd_wrapper.py"]

