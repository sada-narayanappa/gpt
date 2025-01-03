from mangorest.mango import webapi

device = "cpu"
if (torch.cuda.is_available() ):
    device = "cuda"

#--------------------------------------------------------------------------------------------------------    
@webapi("/gpt/test/")
def test(request, **kwargs):
    return "test"
#--------------------------------------------------------------------------------------------------------    
