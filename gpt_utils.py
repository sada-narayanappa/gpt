#!/usr/bin/env python 

import sys, os, torch, logging,datetime, httpx,re, hashlib, json, base64
from ollama import Client
import ollama
from mangorest.mango import webapi
from openai import OpenAI

logger = logging.getLogger( "gpt" )
#------------------------------------------INITIALIZE LLM Stuff -------------------- 
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
        OPENAI_KEY=my_config.OPENAI_KEY
    except:
        pass
#------------------------------------------INITIALIZE the DB-------------------- 
if "/opt/utils/geo_utils/" not in sys.path: sys.path.append("/opt/utils/geo_utils/" )
from services.gen.myjson import myjson

"""
    Clear GPU memory cache for different platforms.
"""
def clear_GPUcache():
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            torch.mps.empty_cache()
        # CPU doesn't need explicit cache clearing
    except Exception as e:
        print(f"Warning: Could not clear cache: {str(e)}")
