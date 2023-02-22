from django.http import HttpResponse
from mangorest.mango import webapi
import os, sys
import openai
sys.path.append(".." )
sys.path.append(os.path.expanduser("~/.django") )
if (os.path.exists(os.path.expanduser("~/.django/my_config.py"))):
    import my_config
    from my_config import *

openai.api_key = my_config.OPENAPI_KEY

@webapi("/gpt/test/")
def test( request, csrfmiddlewaretoken="", **kwargs):
    return kwargs

response={
    "choices": [
        {
        "finish_reason": "stop",
        "index": 0,
        "logprobs": "null",
        "text": " \n\nMy name is Kaitlyn."
        }
    ],
    "created": 1677042132,
    "id": "cmpl-6mbYaLDhuWCyoYMmbGrpDqmmCzPPC",
    "model": "text-davinci-002",
    "object": "text_completion",
    "usage": {
        "completion_tokens": 10,
        "prompt_tokens": 5,
        "total_tokens": 15
    }
}
@webapi("/gpt/testgpt/")
def test( request, **kwargs):
    return response

@webapi("/gpt/callgpt/")
def callgpt(prompt="Hello, my name is", engine="text-davinci-003", max_tokens=100, t=0.5, **kwargs):
    max_tokens = max( 100, int(max_tokens))
    response = openai.Completion.create( engine=engine,  prompt=prompt, max_tokens=max_tokens, temperature=t)
    return response

