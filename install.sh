#!/bin/bash

# Create a temporary directory for compilation
tmp_dir=$(mktemp -d)

# Copy the required modules to the temporary directory
cp secret.py myutils.py configuration.py atengine/atwriter.py chatgpt.py masswriter.py atwoodtypes.py myapp.threads.py retrydialog.py "$tmp_dir"

# Download and install the required spaCy model
python3 -m spacy download es_core_news_sm

# Compile the Python file using PyInstaller
pyinstaller --hidden-import=es_core_news_sm --additional-hooks-dir="$tmp_dir" atwood.py

# Clean up the temporary directory
rm -r "$tmp_dir"
