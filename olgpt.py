import sys, os, ollama, torch, logging,datetime
from ollama import Client
from mangorest.mango import webapi
sys.path.append(os.path.expanduser("~/.django") )
from openai import OpenAI
    
logger = logging.getLogger( "geoapp" )

device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"


OLLAMA_HOST= 'http://10.0.0.29:11434/v1'

if (os.path.exists(os.path.expanduser("~/.django/my_config.py"))):
    import my_config
    try:
        from my_config import OLLAMA_HOST
    except:
        pass

client = OpenAI(
    base_url = OLLAMA_HOST,
    api_key=my_config.OPENAI_KEY
)

OLLAMA = Client(host=OLLAMA_HOST)
logger.info(f"OLLAMA_HOST => {OLLAMA_HOST}")
#--------------------------------------------------------------------------------------------------------    
@webapi("/gpt/generate/")
def ollma_generate(request=None, model="llama3|mistral", prompt="", stream=True,**kwargs):
    logger.info(f"Prepping: {datetime.datetime.now()}")
    model = model.split("|")[0].strip()
    response = OLLAMA.generate(model=model, prompt=prompt, stream=stream)
    # Stream response
    ret = ""
    for chunk in response:
        data = chunk["response"]
        ret += data
        
    logger.debug(ret)
    return ret

#--------------------------------------------------------------------------------------------------------    
@webapi("/gpt/openai/")
def openai(request=None, model="llama3.2|mistral", host="", use_openai="", prompt="", key="", messages="", **kwargs):

    if use_openai or model.startswith('gpt'):
         host= "https://api.openai.com/v1/"
    elif not host:
        host = OLLAMA_HOST
    
    client = OpenAI( base_url = host , api_key = key or my_config.OPENAI_KEY )

    tmsg = [
                {"role": "system"    , "content": "You are a helpful assistant."},
                {"role": "user"      , "content": prompt or "tell a joke?"}
    ]
    
    messages = messages or tmsg
    model    = model.split("|")[0]
    
    logger.info(f"Using host: {host}, {model} : {messages}")
    
    completion = client.chat.completions.create(
        model = model, #"llama3.2",
        messages= tmsg
        )

    ret = completion.choices[0].message
    
    return ret.content
