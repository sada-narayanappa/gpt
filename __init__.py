import os, sys

sys.path.append("/opt/utils/geo_utils/")
try:
    import geoapp.transcribe
    import gpt.index_docs
    import gpt.db_elastic
except Exception as e:
    print(f"\n*******\n***** ERROR LOADING\n{e}\n*******\n*******")
    pass


print ("Initializing web services: " + os.getcwd())
if (os.path.exists("gpt/chatgpt.py")):
    pass
    #from . import chatgpt
    

if (os.path.exists("gpt/whispermod.py")):
    from . import whispermod
    print("whisper Services to be Loaded!")

if (os.path.exists("gpt/olgpt.py")):
    from . import olgpt, extract_text

if (os.path.exists("gpt/diarize.py")):
    from . import diarize

