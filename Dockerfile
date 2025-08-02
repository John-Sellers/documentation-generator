###############################################################################
# Base image
###############################################################################
# Start from the official slim variant of Python 3.10.
# The slim tag gives a smaller image than the regular one, which speeds up
# both network transfer and container startup.
FROM python:3.10-slim

###############################################################################
# Working directory
###############################################################################
# All subsequent commands run relative to /src inside the container.
WORKDIR /src

###############################################################################
# Environment settings
###############################################################################
# Tell Debian to skip any interactive prompts that would otherwise pause
# automated builds. This keeps apt from asking configuration questions.
ENV DEBIAN_FRONTEND=noninteractive

###############################################################################
# System utilities
###############################################################################
# 1. Update the package index.
# 2. Install build-essential (C compiler, linker, and headers) so that any
#    Python packages with native extensions can compile.
# 3. Install git so you can pull private repositories or inspect code in the
#    container if needed.
# 4. Install curl and gnupg which are required to add the NodeSource key later.
# 5. Remove cached apt data to shrink the image.
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

###############################################################################
# Node toolchain
###############################################################################
# Add the NodeSource repository for Node 20 (current long term support).
# Then install nodejs which includes npm.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install pnpm globally with npm.
# pnpm uses hard links to save disk space and speeds up installs compared to npm.
RUN npm install -g pnpm

# Final cleanup of apt to keep the layer small.
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

###############################################################################
# Python dependencies
###############################################################################
# Copy only requirements.txt first so Docker can leverage its layer cache.
COPY requirements.txt .

# Upgrade pip itself for the latest wheel support,
# then install every dependency listed in requirements.txt.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

###############################################################################
# Application source code
###############################################################################
# Copy your actual Python project into the image.
# This comes after the requirements install so that code changes do not
# invalidate the dependency layer, which keeps rebuilds fast.
COPY ./src ./src

###############################################################################
# Default command
###############################################################################
# The container will run your summarization program by default.
# You can override this when using docker run or in devcontainer tasks.
CMD ["python", "src/main.py"]
