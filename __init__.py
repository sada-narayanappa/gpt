import os

print ("Initializing web services: " + os.getcwd())
if (os.path.exists("gpt/chatgpt.py")):
    from . import chatgpt
else:
    print("ChatGPT file does not exist! Were you expecting this?")
    

if (os.path.exists("gpt/whisper.py")):
    from . import whisper
    print("whisper Services Loaded!")
else:
    print("whisper file does not exist! Were you expecting this?")


