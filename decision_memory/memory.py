from rag.vector_store import index,remove
from database.models import Decision

def index_decision(d):
 text=f'Problem: {d.problem} Context: {d.context} Options: {d.options} Decision: {d.decision} Reason: {d.reason} Action: {d.action_taken} Outcome: {d.outcome} Status: {d.status}'
 remove('decision',d.id)
 index('decision',d.id,d.project_id,[text],{'problem':d.problem[:400]})
