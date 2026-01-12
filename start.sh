#!/bin/bash

# Configuration
ENV_NAME="telegram_fetcher_env"
PYTHON_VERSION="3.10"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check for Conda
if ! command_exists conda; then
    echo "Error: Conda is not installed or not in your PATH."
    exit 1
fi

# Initialize conda for the script shell
# This path might need adjustment depending on where conda is installed, 
# but usually 'conda shell.bash hook' works if conda is in PATH.
eval "$(conda shell.bash hook)"

# 2. Check and Create Environment
if conda info --envs | grep -q "$ENV_NAME"; then
    echo "Conda environment '$ENV_NAME' already exists."
else
    echo "Creating Conda environment '$ENV_NAME' with Python $PYTHON_VERSION..."
    conda create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
fi

# 3. Activate Environment
echo "Activating environment '$ENV_NAME'..."
conda activate "$ENV_NAME"

# 4. Install Dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing/Updating dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "Warning: requirements.txt not found."
fi

# 5. Run Application
echo "Starting Telegram Fetcher..."
python main.py
