from datetime import datetime,timezone
WEIGHTS={'semantic':0.55,'problem':0.18,'outcome':0.12,'recency':0.10,'project':0.05}
def score(item,question):
 words=set(question.lower().split());text=set(item['text'].lower().split())
 overlap=len(words&text)/max(len(words),1)
 quality=1 if any(w in item['text'].lower() for w in ['resolved','reduced','successful']) else 0
 return round(WEIGHTS['semantic']*item['similarity']+WEIGHTS['problem']*overlap+WEIGHTS['outcome']*quality+WEIGHTS['recency']*.5+WEIGHTS['project'],4)
