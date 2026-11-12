from rag.vector_store import search
from database.models import Decision

def retrieve(project_id,question):
 matches=search(project_id,question,['decision'])
 ids={d.id:d for d in Decision.query.filter_by(project_id=project_id).all()}
 return [dict(x,decision=ids[x['metadata']['record_id']]) for x in matches if x['metadata']['record_id'] in ids]
