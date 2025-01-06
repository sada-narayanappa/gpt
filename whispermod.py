from mangorest.mango import webapi 
import colabexts
from colabexts import jcommon
import whisper,  os, datetime, librosa, io, soundfile, sys, hashlib, torch
import numpy as np

#-----------------------------models-----------------------------------------------------------------
import platform
device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"
#elif torch.backends.mps.is_available() and platform.processor() =='arm':
#    device = "mps"
#-----------------------------------------------------------------------------------
import threading
mutex        = threading.Lock()
transcriber  = None
def getTranscriber():
    global transcriber, mutex, device
    
    if transcriber is None:
        mutex.acquire()
        if transcriber is None:
            transcriber = whisper.load_model("base", device=device)
        mutex.release()   
    return transcriber
#-----------------------------------------------------------------------------------
def transcribe_file(file ="/Users/snarayan/Desktop/data/audio/index.mp4", **kwargs):
    result = getTranscriber().transcribe(file)
    return result
#-----------------------------------------------------------------------------------
def is_video_file(filename):
    video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"] 
    return os.path.splitext(filename)[1].lower() in video_extensions
#-----------------------------------------------------------------------------------
def is_audio_file(filename):
    audio_extensions = [".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a"] 
    return os.path.splitext(filename)[1].lower() in audio_extensions
# ------------------------------------------------------------------------------
def transcribe(fn, offset=0, duration=60*60, detectSpeakers=0, **kwargs):
    filename = fn
    if (type(fn) == str):
        data, sample_rate = librosa.load(fn, offset=offset, duration=duration, mono=True, sr=16000)
    else:
        filename = "/tmp/bytes.wav"
        content = io.BytesIO(fn)
        data, sample_rate = librosa.load(content,sr=16000, mono=True, offset=offset, duration=duration)
        with open(filename, "wb") as f:
            f.write(fn)

    results = getTranscriber().transcribe(filename, word_timestamps=True)
    txt =""
    for t in results.get('segments', []):
        speaker=""
        if ( detectSpeakers):
            speaker = who(data, t['start'], t['end'], **kwargs)
        o=f"{t['start']:-7.3f} : {t['end']:7.3f} : {speaker} : {t['text']}"
        txt += o + "\n"
    ret = dict(file=filename, trans= results['text'], segs=txt)

    return ret

#--------------------------------------------------------------------------------------------------------    
@webapi("/scribe/transcribe_audio/")
def transcribeAudio(request, **kwargs):
    for f in request.FILES.getlist('file'):
        content = f.read()

    ret = transcribe(content, **kwargs)    
    print(f"Transcribed: {ret}")
    return ret

# ------------------------------------------------------------------------------
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
    from pytube import YouTube
    h = hashlib.md5(url.encode())
    file = "/tmp/" + str(h.hexdigest()) + ".mp4"
    
    if (force_download or not os.path.exists(file)):  
        file = YouTube(url).streams.filter(only_audio=True).first().download(filename=file)

    print( f"File: {file}")
    if (force_transribe or not os.path.exists(file +".txt")):  
        print( f"Calling transcription: {file}.txt")
        tr = getTranscriber().transcribe(file)
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

#--------------------------------------------------------------------------------------------------------    
@webapi("/scribe/transcribe_media/")
def transcribe_media( request, file="", url=None, force_reload="", **kwargs):    
    ret  = [] 
    # STEP 1. extract from file
    for f in request.FILES.getlist('file'):
        content = f.read()
        filename = f"/tmp/{str(f)}"
        print(f"{force_reload} {filename} <==========")
        
        if ( not (is_video_file(filename) or is_audio_file(filename) ) ):
            ret.append (dict(file=filename, trans=f"{filename}: - not a media file", segs="") )
            continue;
        
        filename_trans = f"{filename}.trans"
        filename_segs  = f"{filename}.segs"
        
        if (not force_reload and os.path.exists(filename)):
            if (os.path.exists(filename_trans) and os.path.exists(filename_segs) ):
                with open(filename_trans) as f:
                    trans = f.read()
                with open(filename_segs) as f:
                    segs = f.read()
                    
                ret.append (dict(file=filename, trans= trans, segs=segs))
            else:
                msg = f"{filename}: file exists! have you initiated transcribe! click force"
                ret.append (dict(file=filename, trans=msg, segs="??") )
        else:
            with open(filename, "wb") as f:
                f.write(content)
            results = transcribe_file(filename)
            txt =""
            for t in results['segments']:
                o=f"{t['start']:-7.2f} : {t['end']:7.2f} : {t['text']}"
                txt += o + "\n"
            ret.append (dict(file=filename, trans= results['text'], segs=txt))
            
            with open(filename_trans, "w") as f:
                f.write(results['text'])
            with open(filename_segs, "w") as f:
                f.write(txt)
    
    # STEP 2: transcribe youtube URL when it works
    
    return ret;                

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
