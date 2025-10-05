#!/usr/bin/env python 

import sys, os, torch, logging,datetime, httpx,re, hashlib, json, base64
from ollama import Client
import ollama
from mangorest.mango import webapi
from openai import OpenAI

logger = logging.getLogger( "gpt" )

BASE = os.path.expanduser("~/data/gpt/")

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
from gpt.jsondb import myjson

MYDB = myjson(base=BASE, db='INDICES')
INDEX_TABLE = "indexes"
#------------------------------------------------------------------------------------------ 
@webapi("/gpt/getKBs/")
def getKBs(request=None, **kwargs):
    df = MYDB.read( INDEX_TABLE, nrows=-500)
    ret = {
        'columns': [c for c in df.columns],
        'values' : df.values.tolist()
    }
    return ret
#------------------------------------------------------------------------------------------ 
def isValid(file, **kwargs):
    return True

@webapi("/gpt/deleteKB/")
def deleteKB(request=None, rowid="-1", **kwargs):
    print(locals())
    MYDB.delete(INDEX_TABLE, rowid)
    return getKBs()

@webapi("/gpt/uploadFiles/")
def uploadFiles(request=None, name="test", **kwargs):
    ret = ""
    source_folder=kwargs.get("source_folder", "")
    if ( request):
        for f in request.FILES.getlist('file'):
            content = f.read()
            if ( not source_folder):
                basedir =  f"{BASE}/{name}-files/"
            else:
                basedir =  f"{BASE}/{source_folder}/"
            os.makedirs(basedir, exist_ok=True)
            filename = f"{basedir}/{str(f)}"

            ret += f"{filename} => uploading \n"
            if ( isValid(name, **kwargs)):
                with open(filename, "wb") as f:
                    f.write(content)
            
    return ret

def indexFiles(request, **kwargs):
    cmd = ""
    if (  len(request.FILES) > 0):
        v = [kwargs.get(k, "") for k in "source_folder es_url es_user es_pass index_name model".split()]
        v[0] = f"{BASE}/{v[0]}"     # Application specif folder

        vision_index=kwargs.get("vision_index", "")
        if ( not vision_index ):
            cmd = f"gpt/db_elastic.py -p {v[0]} -e {v[1]} -u '{v[2]}' -w '{v[3]}' -i {v[4]} -m {v[5]}"

        if ( vision_index ):
            cmd = f"gpt/db_vision.py -p {v[0]} "
            pass

    if (cmd):
        logger.info("Executing " + cmd)
        os.system(cmd + " &")


@webapi("/gpt/createUpdateKB/")
def createUpdateKB(request=None,  **kwargs):
    MYDB.create_table(INDEX_TABLE)
    df = MYDB.update( INDEX_TABLE, kwargs)

    # index_name must be sent
    index_name = kwargs.get("index_name")

    ret = uploadFiles(request, index_name, **kwargs)            
    indexFiles(request, **kwargs)

    return getKBs()


@webapi("/gpt/searchKB/")
def searchKB(request=None,  **kwargs):
    import db_elastic, db_vision
    keys = "source_folder query vision_index model".split()
    [path, query, v,model] = [kwargs.get(k, "") for k in keys]
    path = f"{BASE}/{path}"     # Application specif folder

    if ( v ):
        resp = db_vision.queryVision(query, path, model=model)
        ret  = [dict(page_content=resp, metadata="None")]
    else:
        ret = db_elastic.esSearchIndex(request, **kwargs)

    return ret
    pass;

