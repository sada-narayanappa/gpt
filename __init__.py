import os, sys

print ("Initializing web services: " + os.getcwd())
if (os.path.exists("gpt/chatgpt.py")):
    pass
    #from . import chatgpt
else:
    print("ChatGPT file does not exist! Were you expecting this?")
    

if (os.path.exists("gpt/whispermod.py")):
    #from . import whispermod
    print("whisper Services to be Loaded!")
else:
    print("whisper file does not exist! Were you expecting this?")


