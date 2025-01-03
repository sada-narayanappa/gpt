from elasticsearch import Elasticsearch
from typing import Any, Dict, Optional, List

# --------------------------------------------------------------------------------
import sys, os, ollama, torch, logging,datetime, requests,re, hashlib
from ollama import Client
from mangorest.mango import webapi
    
logger = logging.getLogger( "myapp" )
device = "cpu"

if (torch.cuda.is_available() ):
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"

OLLAMA_HOST= 'http://127.0.0.1:11434/v1'
OPENAI_KEY = "NO KEY"

sys.path.append(os.path.expanduser("~/.django") )
if (os.path.exists(os.path.expanduser("~/.django/my_config.py"))):
    import my_config
    try:
        from my_config import OLLAMA_HOST
    except:
        pass

MODEL= "ollama3.2"
# --------------------------------------------------------------------------------
# Function to get embedding using OLLAMA API
# Generate embeddings for a given text using the OLLAMA API.
#
def get_ollama_embedding(text: str, model: str =MODEL) -> List[float]:
    url = "http://localhost:11434/api/embeddings"
    payload = {"model": model, "prompt": text}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        embedding = response.json().get("embedding", [])
        return embedding
    else:
        raise Exception(f"Failed to get embedding: {response.text}")

#query_embedding = get_ollama_embedding(query_text, model=model )
