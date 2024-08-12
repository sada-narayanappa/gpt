import sys, os, ollama, torch, logging,datetime
from ollama import Client
from mangorest.mango import webapi
sys.path.append(os.path.expanduser("~/.django") )
    
logger = logging.getLogger( "geoapp" )
device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"


OLLAMA_HOST= 'http://10.0.0.29:11434'
OLLAMA_HOST= 'http://67.162.141.146:11434'
OLLAMA_HOST=None
if (os.path.exists(os.path.expanduser("~/.django/my_config.py"))):
    import my_config
    from my_config import OLLAMA_HOST

OLLAMA = Client(host=OLLAMA_HOST)
#OLLAMA = Client()
#--------------------------------------------------------------------------------------------------------    
@webapi("/ollama/generate/")
def ollma_generate(request=None, model="mistral", prompt="", stream=True,**kwargs):
    logger.info(f"Prepping: {datetime.datetime.now()}")
    response = OLLAMA.generate(model=model, prompt=prompt, stream=stream)
    # Stream response
    ret = ""
    for chunk in response:
        data = chunk["response"]
        ret += data
        
    logger.debug(ret)
    return ret

