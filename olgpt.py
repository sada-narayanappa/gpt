import sys, os, torch, logging,datetime, httpx,re, hashlib, json, base64
import ollama
from ollama import Client
from mangorest.mango import webapi
from openai import OpenAI
    
logger = logging.getLogger( "geoapp" )

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
#------------------------------------------------------------------------------------------    
import socket
from urllib.parse import urlparse

def is_host_reachable(host, timeout=0.1):
    url = urlparse(host)
    host, port = url.hostname, (url.port or 80)
    print(f"Trying {host} {port}")
    try:
        socket.create_connection((host, port), timeout)
        return True
    except ConnectionRefusedError as e:
        print("Connection refused.")
        return False
    except OSError as e:
        print("OS error: {0}".format(e))
        return False
    
if ( not os.environ.get('http_proxy','') or not is_host_reachable(os.environ['http_proxy']) ):
    proxies = None
else:
    proxies = dict(
        http_proxy = os.environ.get('http_proxy',''),
        https_proxy= os.environ.get('https_proxy',''),
        #no_proxy= os.environ.get('no_proxy','')
    )
    proxies = {
        #"http_proxy://"  : os.environ.get('http_proxy',''),
        #"https_proxy://" : os.environ.get('https_proxy',''),
        #"no_proxy": os.environ.get('no_proxy','')
    }
    print(f"\n******PROXIES ********\n{proxies}\n*******")
#-----------------------------------------------------------------------------------------    
def getClient(host=OLLAMA_HOST, key=None, proxies=proxies):
    client = OpenAI( base_url = host , 
                api_key = key or my_config.OPENAI_KEY,
                http_client=httpx.Client(
                    proxies=proxies,
                    transport=httpx.HTTPTransport(local_address="0.0.0.0"),
                    verify=False
                ),
            )
    return client
#-----------------------------------------------------------------------------------------    
@webapi("/gpt/generate/")
def ollma_generate(request=None, model="llama3|mistral", prompt="", stream=True,**kwargs):
    OLLAMA = Client(host=OLLAMA_HOST)
    logger.info(f"OLLAMA_HOST => {OLLAMA_HOST}  Prepping: {datetime.datetime.now()}")
    
    model = model.split("|")[0].strip()
    response = OLLAMA.generate(model=model, prompt=prompt, stream=stream)
    # Stream response
    ret = ""
    for chunk in response:
        data = chunk["response"]
        ret += data
        
    logger.debug(ret)
    return ret
#-------------------------------------------------------------------------------------------    
def tob64(imageFile):
    with open(imageFile, "rb") as f:
        b64Image = base64.b64encode(f.read()).decode("utf-8")
    return b64Image

@webapi("/gpt/llmVision/")
def llmVision(request=None, model="llama3.2-vision|llama3.2-vision:90b", 
                file="", messages=None, prompt="", **kwargs):

    OLLAMA = Client(host=OLLAMA_HOST)
    if ( request and not file and not messages):
        for f in request.FILES.getlist('file'):
            context = f.read()
            #fileIO = io.BytesIO(content)
            file = f"/tmp/{str(f)}"
            with open(file, "wb") as f:
                f.write(context)
            #context = open(file, "rb").read()
            #context = tob64(file)      
            break;      
    elif(not messages):
        #file  = "/tmp/people.jpg"
        #q = "what is in this image"
        context = open(file, "rb").read()
        #context = tob64(file)
        messages= [ 
            dict(role="user", content=prompt, images=[context])
        ]
    else:
        if ( type(messages) == str) :
            messages = json.loads(messages)

    #print(messages)
    resp = ollama.chat( model= model, messages=messages)

    return resp.message.content

#-------------------------------------------------------------------------------------------    
@webapi("/gpt/openai/")
def openaicall(**kwargs):
    return llm(**kwargs)

@webapi("/gpt/llm/")
def llm(request=None, model="llama3.2|mistral", host="", use_openai="", prompt="", 
                key="", messages="", temp=None, max_tokens=None, top_p=None, **kwargs):

    if use_openai or model.startswith('gpt'):
         host= "https://api.openai.com/v1/"
    elif not host:
        host = OLLAMA_HOST
    client = getClient(host)
        
    tmsg = [
                {"role": "system"    , "content": "You are a helpful assistant."},
                {"role": "user"      , "content": prompt or "tell a joke?"}
    ]

    if (not messages):
        messages = tmsg

    if ( type(messages) == str) :
        messages = json.loads(messages)
    

    model    = model.split("|")[0]
    
    logger.info(f"Using host: {host}, {model} : {messages}")
    
    completion = client.chat.completions.create(model=model, messages=messages, 
                                                temperature=temp, max_tokens=max_tokens )

    ret = completion.choices[0].message
    
    return ret.content
#-------------------------------------------------------------------------------------------    
@webapi("/gpt/test/")
def test(request=None, model="llama3.2|mistral", info=None, **kwargs):
    import json
    logger.info(f"{model} : info: {info} {type(info)} {kwargs}")

    if (info):
        infoj = json.loads(info)
        print(f"INFORMATION: {infoj}")
    return "OK"

#-------------------------------------------------------------------------------------------    
@webapi("/gpt/getLLMModels/")
def getLLMModels(request=None, model="llama3.2|mistral", info=None, **kwargs):

    list = []
    models = ollama.list()
    for m in models.models:
        list.append(m.model)

    list = list + "gpt-3.5-turbo gpt-4o".split()
    list.sort()
    return list
#--------------------------------------------------------------------------------------------    
# See: for voice options: https://platform.openai.com/docs/guides/text-to-speech
# alloy is our default
@webapi("/gpt/tts/")
def openaitts(request=None, prompt="", voice="alloy", fname_prefix="aud_", force="", **kwargs):
    #client = OpenAI( api_key = my_config.OPENAI_KEY)
    client = getClient(host="https://api.openai.com/v1/")

    basedir="static/data/tmp/"
    os.makedirs(basedir, exist_ok=True)
    
    fnames = []
    prompts= []
    segs = re.split("\\s*\n\\s*#\\s*---+.*\n\\s*", prompt, flags=re.MULTILINE)
    
    for i, s in enumerate(segs):
        s = s.strip();        
        if ( not s):
            continue
        
        h = hashlib.md5(s.encode()).hexdigest()
        speech_file_path = f"{basedir}{fname_prefix}_{h}.mp3"
        if ( os.path.exists(speech_file_path) and not force):
            logger.info(f"===> {speech_file_path} exists!")
            fnames.append(speech_file_path)
            continue
        
        with client.audio.speech.with_streaming_response.create(
                model="tts-1",  speed=1, voice=voice,  input=s ) as response:
            response.stream_to_file(speech_file_path)
        
        fnames.append(speech_file_path)
        prompts.append(s)
    
    return dict(voice=voice, input=prompts, files=fnames)

#-----------------------------------------------------------------------------------------    
