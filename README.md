# CHATGPT 

Some exporations 




------------------------------------------------------------------------------
# Vision RAG 
------------------------------------------------------------------------------


Start colpali server:

```
    docker run --gpus all --rm -p 8081:8080 -v /disk01/e359669/colpali-testbench/model:/mnt/models -e ADAPTER_PATH=/mnt/models/colpali -e MODEL_PATH=/mnt/models/colpaligemma colpali
```