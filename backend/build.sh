#!/usr/bin/env bash
set -e
pip install -r requirements.txt

# Pre-download the embedding model
python -c "
from fastembed import TextEmbedding
print('Downloading embedding model...')
list(TextEmbedding('sentence-transformers/all-MiniLM-L6-v2').embed(['warmup']))
print('Model ready.')
"
