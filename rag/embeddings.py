from functools import lru_cache
from flask import current_app
@lru_cache(maxsize=2)
def _load(name):
 from sentence_transformers import SentenceTransformer
 return SentenceTransformer(name,local_files_only=False)
def embed(texts):
 model=_load(current_app.config['EMBEDDING_MODEL'])
 return model.encode(texts,normalize_embeddings=True).tolist()
