import ollama, torch, logging,datetime
from ollama import Client
from mangorest.mango import webapi

logger = logging.getLogger( "geoapp" )
device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"


OLLAMA = Client(host='http://localhost:11434')
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
