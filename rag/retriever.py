from database.models import Document,PermissionRequest
from rag.vector_store import search

def can_read(user,doc):
 if user.role=='Admin':return True
 if not doc.restricted:return True
 return PermissionRequest.query.filter_by(user_id=user.id,document_id=doc.id,status='approved').first() is not None

def retrieve(user,project_id,question):
 found=search(project_id,question,['document'])
 docs={d.id:d for d in Document.query.filter_by(project_id=project_id,status='indexed').all()}
 return [x for x in found if (doc:=docs.get(x['metadata']['record_id'])) and can_read(user,doc)]
