import os, sys
import geoapp.transcribe

print ("Initializing web services: " + os.getcwd())
if (os.path.exists("gpt/chatgpt.py")):
    pass
    #from . import chatgpt
    

if (os.path.exists("gpt/whispermod.py")):
    from . import whispermod
    print("whisper Services to be Loaded!")

if (os.path.exists("gpt/olgpt.py")):
    from . import olgpt

if (os.path.exists("gpt/diarize.py")):
    from . import diarize

