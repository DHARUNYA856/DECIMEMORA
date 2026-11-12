import requests
from flask import current_app

def generate(prompt):
 try:
  r=requests.post(current_app.config['OLLAMA_URL'].rstrip('/')+'/api/generate',json={'model':current_app.config['OLLAMA_MODEL'],'prompt':prompt,'stream':False,'options':{'num_ctx':4096}},timeout=120)
  r.raise_for_status();return r.json().get('response','No response returned.')
 except requests.exceptions.Timeout:return 'The local model timed out. Try a shorter question.'
 except requests.exceptions.RequestException:return 'Local Ollama is unavailable or the Qwen model is not installed. Start Ollama and run: ollama pull qwen2.5:3b'
