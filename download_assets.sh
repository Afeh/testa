#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Define the file name and the direct download URL
FILE_NAME="shape_predictor_68_face_landmarks.dat"
DOWNLOAD_URL="https://drive.google.com/uc?export=download&id=1XSyHUy7SiFYh3MQI9Y2e_Oieu8TPW28f"

# Check if the file already exists
if [ -f "$FILE_NAME" ]; then
    echo "$FILE_NAME already exists, skipping download."
else
    echo "$FILE_NAME not found, downloading..."
    # Use wget to download the file. The -O flag specifies the output file name.
    # The --no-check-certificate flag can help avoid issues with SSL on some systems.
    wget -O "$FILE_NAME" --no-check-certificate "$DOWNLOAD_URL"
    echo "Download complete."
fi