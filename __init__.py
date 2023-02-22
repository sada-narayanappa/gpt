import os

print ("Initializing web services: " + os.getcwd())
if (os.path.exists("chatgpt/chatgpt.py")):
    from . import chatgpt
else:
    print("ChatGPT file does not exist! Were you expecting this?")
    

