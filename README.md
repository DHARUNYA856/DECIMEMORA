# DeciMemora

Local organizational knowledge preservation and decision intelligence platform. Built with Python 3.11, Flask, SQLite, ChromaDB, Sentence Transformers, Ollama and Qwen 2.5 3B. No paid API or cloud account is required.

## Features
Admin-created users; five roles; active/inactive accounts; project membership with read/write/manage access; PDF/DOCX/TXT indexing; restricted-document approvals; project-specific vector search; structured and semantic decision memory; combined relevance ranking; local Qwen answers with references; project-specific chat history; CSRF protection.

## Architecture
Flask routes -> SQLite permissions -> authorized document and decision vector search -> relevance scoring -> evidence context + recent chat -> local Ollama/Qwen -> answer, sources and chat history. Documents and decisions have separate Chroma kind metadata. Restricted document hits are filtered before entering the LLM prompt.

## Windows PowerShell installation
Install Python 3.11 and Ollama first. Open VS Code terminal in the extracted folder:

```powershell
cd D:\DeciMemora
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`: set a strong unique `SECRET_KEY` and `ADMIN_PASSWORD` before first run. Download the embedding model while online:

```powershell
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
ollama pull qwen2.5:3b
python app.py
```

Visit http://127.0.0.1:5000 . Ollama normally runs as a local service; if not, start `ollama serve` in another terminal. Once dependencies and models are cached, normal usage does not require internet. For strictly offline embedding loads, ensure the model is cached locally before disconnecting.

## Initial login
Username: `admin`. Password: the `ADMIN_PASSWORD` value in `.env` (example template: `ChangeMe@12345`). Change it before the first run. To change the password later, edit the user through Admin > Employees. Changing the environment variable alone will not reset an existing account. There is no public registration.

## Full demo
1. Log in as admin. The `BANK-001` Banking Payment System project and example decision are created on first startup.
2. Upload `sample_data/Payment_API_Troubleshooting.txt` to BANK-001. Confirm status `indexed`.
3. Create Arun (EMP001) and a New Employee (EMP002), giving each a unique password.
4. In Projects > Members, assign both to BANK-001.
5. Sign out and log in as EMP002. Select BANK-001 in Ask DeciMemora.
6. Ask `Why is the payment API failing?`, then `Why did they choose retry instead of changing the provider?`
7. Review source and decision references. The follow-up includes recent project-specific questions in retrieval.
8. For restricted access demo, upload a second file with Restricted selected. Employee requests permission in Documents; admin approves in Access Requests; employee can then download it and its indexed content becomes eligible for RAG.

## Permissions and security
Admin routes require Admin role. Employee project selection is checked on the backend. Project memberships control project visibility; document restrictions are checked again after vector retrieval. Every POST requires a session CSRF token. Uploads have extension and size checks, random stored filenames and secure displayed names. Passwords are hashed. Keep the app on localhost; use HTTPS, malware scanning, stronger MIME/content validation, audit logging and a production server before any organizational deployment.

## Files and data
`database/models.py` defines the SQLite schema: User, Project, ProjectMember, Document, PermissionRequest, Decision and ChatHistory. The local SQLite file is created under `instance/` for the default URI. Chroma persists under `chroma_db/`; uploads are under `uploads/`. These are ignored by Git. The sample decisions JSON is illustrative; the seeded SQLite decision must be indexed before semantic retrieval (edit/save it in the admin UI after downloading the embedding model).

## RAG, decision memory and ranking
Uploaded text is extracted with PyMuPDF, python-docx or UTF-8, chunked with overlap and embedded by all-MiniLM-L6-v2. Decision fields are combined and embedded in the same project-scoped vector store with kind `decision`. Query engine gathers permitted chunks and decisions, applies semantic/keyword/outcome/recency/project weights in `query/relevance.py`, then sends bounded evidence and recent chat to Qwen via Ollama. Known evidence is separated from recommended actions. Retrieval is not a guarantee of factual correctness; verify answers against source documents.

## Troubleshooting
- `py -3.11` not found: install Python 3.11 and ensure Python Launcher is available.
- PowerShell activation blocked: run `Set-ExecutionPolicy -Scope Process Bypass` and retry activation.
- Ollama unavailable: run `ollama serve` and `ollama pull qwen2.5:3b`.
- Model unavailable offline: download both Qwen and the embedding model while online.
- Indexing failed: check the uploaded file is text-readable and local disk space is available. Image-only PDFs require OCR (not included).
- Slow first answer: the Qwen 3B model may be slow on CPU-only laptops; close other applications.
- Port occupied: stop the conflicting process or change the port in `app.py`.

## Git
```powershell
git init
git add .
git commit -m "Initial DeciMemora application"
```

## Testing and future improvements
Run `python -m unittest discover -s tests`. Test admin/employee login, denied admin access, project membership isolation, restricted-document approval, file extraction, document indexing, decision retrieval, Ollama response and follow-up history. Integration tests involving embeddings and Qwen require downloaded local models. Future improvements: audit trail, secure backup/restore, granular role capabilities, virus scanning, full-text keyword fallback, configurable ranking UI, and evaluation metrics.
