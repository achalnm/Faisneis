#!/usr/bin/env bash
set -e
pip install -r requirements.txt
python -c "
from fastembed import TextEmbedding
list(TextEmbedding('sentence-transformers/all-MiniLM-L6-v2').embed(['warmup']))
print('model ready')
"
