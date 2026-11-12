import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ROOT=Path(__file__).resolve().parent
class Config:
 SECRET_KEY=os.getenv('SECRET_KEY','dev-only-change-before-use')
 SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///decimemora.db')
 SQLALCHEMY_TRACK_MODIFICATIONS=False
 MAX_CONTENT_LENGTH=int(os.getenv('MAX_CONTENT_LENGTH','10485760'))
 UPLOAD_FOLDER=str(ROOT/os.getenv('UPLOAD_FOLDER','uploads'))
 CHROMA_PATH=str(ROOT/os.getenv('CHROMA_PATH','chroma_db'))
 OLLAMA_URL=os.getenv('OLLAMA_URL','http://localhost:11434')
 OLLAMA_MODEL=os.getenv('OLLAMA_MODEL','qwen2.5:3b')
 EMBEDDING_MODEL=os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2')
