from pathlib import Path
import fitz
from docx import Document as Docx

def extract(path):
 path=Path(path);ext=path.suffix.lower()
 if ext=='.pdf':
  with fitz.open(path) as doc:return '\n'.join(page.get_text() for page in doc)
 if ext=='.docx':return '\n'.join(p.text for p in Docx(path).paragraphs)
 if ext=='.txt':return path.read_text(encoding='utf-8-sig')
 raise ValueError('Unsupported document type')
def chunks(text,size=900,overlap=150):
 text=' '.join(text.split());step=size-overlap
 return [text[i:i+size] for i in range(0,len(text),step) if text[i:i+size].strip()]
