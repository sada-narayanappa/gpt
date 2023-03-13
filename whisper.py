from mangorest.mango import webapi 
import colabexts
from colabexts import jcommon
import whisper,  os, datetime, librosa, io, soundfile, sys
import threading
import numpy as np

sys.path.append("../..")
sys.path.append("..")

model  = None
device = "cpu"
mutex  = threading.Lock()

def getmodel():
    global model, mutex
    
    if model is None:
        mutex.acquire()
        if model is None:
            model = whisper.load_model("base")
        mutex.release()   
    return model

def transcribe_file(file ="/Users/snarayan/Desktop/data/audio/index.mp4", **kwargs):
    result = getmodel().transcribe(file)
    return result

def splitIntoParas(tr, nLinesPerPara=4):
    n= nLinesPerPara
    l=tr.get('segments', [])
    ret = ""
    for i,j in enumerate(l[::n]):
        a, b = i*n, i*n + n
        o = "".join([j['text'] for j in l[a:b]])
        ret += o.strip() + "\n\n";
        #print(f'{a}-{b} {o} \n')
        
    return ret
#-----------------------------------------------------------------------------------
def who(data, start=0, end=None, **kwargs):
    try:
        import scribe.notebooks.speaker as speaker
        top3, tops = speaker.whoisInAudio1(data, top=3, start=start, end=end, **kwargs  )
        ret =  { 
            'top3'    : ";".join(top3[::-1]) ,
            'topScore': ""+str(tops)
        }
    except Exception as e:
        print("ERROR: " , e)
        ret = {'top3': ";;", 'topScore': 0}

    return ret
# ------------------------------------------------------------------------------
def transcribe(fn, offset=0, duration=60*60, detectSpeakers=1, **kwargs):
    if (type(fn) == str):
        data, sample_rate = librosa.load(fn, offset=offset, duration=duration, mono=True, sr=16000)
    else:
        content = io.BytesIO(fn)
        data, sample_rate = librosa.load(content,sr=16000, mono=True, offset=offset, duration=duration)

    ret = getmodel().transcribe(data)
    for s in ret.get('segments', []):
        s.pop('tokens')
        if ( detectSpeakers):
            speaker = who(data, s.get('start'), s.get('end'), **kwargs)
            s['speakers'] = [speaker]

    return ret

@webapi("/scribe/stt3/")
def transcribe2(request, **kwargs):
    for f in request.FILES.getlist('file'):
        content = f.read()

    ret = transcribe(content, **kwargs)    
    print(f"Transcribed: {ret}")
    return ret

@webapi("/scribe/convert2wav/")
def convert2wav(request, **kwargs):
    for f in request.FILES.getlist('file'):
        content = f.read()

    content = io.BytesIO(content)
    data, sample_rate = librosa.load(content,sr=16000, mono=True, offset=offset, duration=duration)

    #offset, duration, file = 0, None, "/tmp/test1.wav"
    #data, sample_rate = librosa.load(file, offset=offset, duration=duration, mono=True, sr=16000)
    ret = io.BytesIO()
    soundfile.write("/tmp/_tmp.wav", data, samplerate=16000)
    with open("/tmp/_tmp.wav", "rb") as f:
        ret.write(f.read())
    return ret
#--------------------------------------------------------------------------------------------------------    
test_url = "https://www.youtube.com/watch?v=DuSDVj9a4WM&list=PLEpvS3HCVQ5_ZlyF1_i-WSwBzLoDLxoc9"

@webapi("/scribe/transcribe_youtube/")
def transcribe_youtube( url = test_url , force_download=False, force_transribe=False, **kwargs):    
    h = hashlib.md5(url.encode())
    file = "/tmp/" + str(h.hexdigest()) + ".mp4"
    
    if (force_download or not os.path.exists(file)):  
        file = YouTube(url).streams.filter(only_audio=True).first().download(filename=file)

    print( f"File: {file}")
    if (force_transribe or not os.path.exists(file +".txt")):  
        print( f"Calling transcription: {file}.txt")
        tr = getmodel().transcribe(file)
        ret = splitIntoParas(tr)
        with open(file +".txt", "w") as f:
            f.write(ret)
        with open(file +".json", "w") as f:
            f.write(str(tr))
            
        transcription = ret
    else:
        with open(file +".txt", "r") as f:
            transcription = f.read()
        
    return transcription;

#-----------------------------------------------------------------------------------    
def process(sysargs):
    print("Parsing and processing")
    
    if (sysargs.url.strip()):
        print( f"Transcribing {sysargs.url}")
        transcribe_youtube(sysargs.url.strip())
    
#-----------------------------------------------------------------------------------
sysargs=None
def addargs():
    global sysargs
    p = argparse.ArgumentParser(f"{os.path.basename(sys.argv[0])}:")
    p.add_argument('-u', '--url', type=str, default="", help="Youtube URL")
    try:
        sysargs, unknown=p.parse_known_args(sys.argv[1:])
    except argparse.ArgumentError as exc:
        print(exc.message )
        
    if (unknown):
        print("Unknown options: ", unknown)
        #p.print_help()
    return sysargs    
#-----------------------------------------------------------------------------------
if __name__ == '__main__':
    if (not colabexts.jcommon.inJupyter()):
        t1 = datetime.datetime.now()
        sysargs = addargs()
        ret = process(sysargs)
        t2 = datetime.datetime.now()
        print(f"#All Done in {str(t2-t1)} ***")
    else:
        pass
