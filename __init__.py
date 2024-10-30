import os, sys

print ("Initializing web services: " + os.getcwd())
if (os.path.exists("gpt/chatgpt.py")):
    pass
    #from . import chatgpt
    

if (os.path.exists("gpt/whispermod.py")):
    #from . import whispermod
    print("whisper Services to be Loaded!")

if (os.path.exists("gpt/olgpt.py")):
	pass
    #from . import olgpt


