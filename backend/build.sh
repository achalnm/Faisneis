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

# Pre-build CSO catalog + embeddings so the running server never has to do it
python -c "
from pathlib import Path
from app.stats.cso_catalog import build_catalog, _load_or_build_embeddings
cache = Path('./data/cache')
cache.mkdir(parents=True, exist_ok=True)
catalog = build_catalog(cache)
_load_or_build_embeddings(catalog, cache)
print(f'CSO catalog ready: {len(catalog)} tables')
"
