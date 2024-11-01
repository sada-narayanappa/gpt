import ollama, torch, logging
from mangorest.mango import webapi

device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"

logger = logging.getLogger( "geoapp" )
#--------------------------------------------------------------------------------------------------------    
@webapi("/ollama/generate/")
def ollma_generate(request=None, model="mistral", prompt="", stream=True,**kwargs):
    response = ollama.generate(model=model, prompt=prompt, stream=stream)
    # Stream response
    ret = ""
    for chunk in response:
        data = chunk["response"]
        ret += data
        
    logger.debug(ret)
    return ret

ollma_generate(prompt="whos is the chief data scientist of Lockheed Martn", stream=True)   
    
