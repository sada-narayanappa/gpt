#!/usr/bin/env python
import os, torch
from pyannote.audio import Pipeline
from pathlib import Path

device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"
elif torch.backends.mps.is_available():
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

path=searchfor()
diarizer=None
if ( path ):
    diarizer = getdiarizerLocal(path)
else:
    print("Model not found")
# -----------------------------------------------------------------------------
def diarize(request=None,file="/tmp/test_multiple.wav", nspeakers=None ):
    diarization = diarizer(file, num_speakers=nspeakers)
    ret = "[\n"
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        #print(f'Speaker "{speaker}" - "{segment}"')
        id = int(speaker.split('_')[1])
        ret +=f'{{start: {segment.start}, end: {segment.end}, label: {id} }}\n'
        
    ret += "]"
    return ret
