from flask import abort
from database.db import db
from database.models import Project,ChatHistory
from rag.retriever import retrieve as documents
from decision_memory.retriever import retrieve as decisions
from query.relevance import score
from query.context_builder import build
from llm.ollama import generate
from employee.routes import project_access

def answer_query(user,project_id,question):
 project=Project.query.get_or_404(project_id)
 if not project_access(user,project_id):abort(403)
 history=ChatHistory.query.filter_by(user_id=user.id,project_id=project_id).order_by(ChatHistory.id.desc()).limit(4).all()
 expanded=question+' '+(' '.join(h.question for h in history[:2]) if len(question.split())<9 else '')
 doc_hits=documents(user,project_id,expanded)
 dec_hits=decisions(project_id,expanded)
 items=[dict(x,kind='Document',label=x['metadata'].get('file_name','Document')) for x in doc_hits]
 items += [dict(x,kind='Decision',label=x['decision'].problem) for x in dec_hits]
 for x in items:x['score']=score(x,expanded)
 items=sorted(items,key=lambda x:x['score'],reverse=True)[:9]
 answer=generate(build(project,question,items,history)) if items else 'No authorized organizational evidence was found for this question. Please ask your project administrator to add relevant documents or decisions.'
 db.session.add(ChatHistory(user_id=user.id,project_id=project_id,question=question,answer=answer));db.session.commit()
 return {'answer':answer,'sources':[{'name':x['label'],'score':x['score']} for x in items if x['kind']=='Document'],'decisions':[{'problem':x['decision'].problem,'decision':x['decision'].decision,'outcome':x['decision'].outcome} for x in items if x['kind']=='Decision'],'cases':[{'problem':x['decision'].problem,'solution':x['decision'].action_taken,'status':x['decision'].status} for x in items if x['kind']=='Decision']}
