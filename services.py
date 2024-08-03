from django.http import HttpResponse
from mangorest.mango import webapi
from transformers import pipeline

device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"

#--------------------------------------------------------------------------------------------------------    
@webapi("/gpt/test/")
def test(request, **kwargs):
    return "test"
#--------------------------------------------------------------------------------------------------------    
