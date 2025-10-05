#!/usr/bin/env python 

import sys, os, torch, logging

logger = logging.getLogger( "gpt" )
#------------------------------------------INITIALIZE LLM Stuff -------------------- 
device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"

OLLAMA_HOST= 'http://127.0.0.1:11434/v1'
OPENAI_KEY = "NO KEY"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
try:
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv("./.env"))
except ImportError:
    print("dotenv not found!, skipping...")


if os.path.exists("my_config.py"):
    import my_config
    from my_config import *
else:
    home_env = os.path.expanduser("~/.django/")
    home_con = home_env+ "/my_config.py"
    if not (home_env in sys.path):
        sys.path.append(home_env)

    if os.path.exists(home_con):
        import my_config
        from my_config import *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def get_from_env_or_config(key):
    v = os.environ.get(key, "")
    if (v):
        return v
    try:
        v = vars(my_config).get(key)
        return v
    except:
        return None
#------------------------------------------INITIALIZE the DB-------------------- 
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
