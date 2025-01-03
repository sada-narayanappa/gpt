#!/usr/bin/env python
import os, torch
from pyannote.audio import Pipeline
from pathlib import Path
from mangorest.mango import webapi 
import platform; 

device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"
elif torch.backends.mps.is_available() and platform.processor() =='arm':
    device = "mps"
# -----------------------------------------------------------------------------
diarizer = None
def getdiarizer():
    global diarizer 
    if ( diarizer is not None):
        return diarizer

    atoken = "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"
    model  = "pyannote/speaker-diarization-3.0"
    #pipeline = Pipeline.from_pretrained(model, use_auth_token=atoken)
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0")
    pipeline.to(torch.device(device) )
    
    diarizer = pipeline
    return diarizer

''' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Searches for the directory containg this app
'''
def searchfor(loc="models/pyannote.yml", max_depth=2):
    if ( os.path.exists(loc)):
        return loc
    cwd = Path.cwd().resolve() 
    for i in range(max_depth):
        loc= f"../{loc}"
        print(f"Trying {loc} - {cwd} ")
        if ( os.path.exists(loc) ):
            return loc
    return ""
    
def getdiarizerLocal(path_to_config: str | Path) -> Pipeline:
    global diarizer 
    if ( diarizer is not None):
        return diarizer
    path_to_config = Path(path_to_config)
    cwd = Path.cwd().resolve()  # store current working directory

    print(f"Loading pyannote pipeline from {path_to_config}... CWD: {cwd}")
    # the paths in the config are relative to the current working directory
    # so we need to change the working directory to the model path
    # and then change it back

    # first .parent is the folder of the config, second .parent is the folder containing the 'models' folder
    cd_to = path_to_config.parent.parent.resolve()
    print(f"Changing working directory to {cd_to}")
    os.chdir(cd_to)

    pipeline = Pipeline.from_pretrained(path_to_config)
    print(f"Changing working directory back to {cwd}")
    os.chdir(cwd)

    pipeline.to(torch.device(device) )
    diarizer = pipeline
    return diarizer

try:
    dir = os.path.dirname(__file__)
    path= f'{dir}/models/pyannote.yml'
except:
    path="models/pyannote.yml"
    pass
path=searchfor(path)
diarizer=None
if ( path ):
    diarizer = getdiarizerLocal(path)
else:
    print("Model not found")
# -----------------------------------------------------------------------------
'''
Diarize first file sent in
'''
@webapi("/scribe/diarize/")
def diarize(request=None,file="/tmp/test_multiple.wav", nspeakers=None, **kwargs ):
    print(f"<============= {file} n={nspeakers} {kwargs}" )
    global diarizer
    if ( not diarizer) :
        return "Sorry - diarizer not loaded!"

    if ( request and len(request.FILES) > 0):
        for f in request.FILES.getlist('file'):
            content = f.read()
            file = f"/tmp/{str(f)}"
            with open(file, "wb") as f:
                f.write(content)
            break; #lets do one file at a time now
    elif (type(file) == str):
        pass # Cool this is what we wanted
    else:
        pass
        # filename="/tmp/diarize.wav"
        # with open(filename, "wb") as f:
        #     f.write(file)
        # file = filename

    print(f"<============= {file} n={nspeakers} {kwargs}" )
    diarization = diarizer(file, num_speakers= nspeakers or None )
    ret = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        #print(f'Speaker "{speaker}" - "{segment}"')
        id = int(speaker.split('_')[1])
        e = dict(start=segment.start, end = segment.end, label=id)
        ret.append(e)
        
    return ret
