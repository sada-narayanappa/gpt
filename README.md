# GenAI Studio experiments

## Installation
Install ollama from ollama.com
Download the following models:
```
 [ ] 
    ollama pull qwen2.5:latest 
    ollama pull qwen2:latest
    ollama pull all-minilm:L6-v2 
    ollama pull all-minilm:latest 
    ollama pull granite3-dense:8b  
    ollama pull llama3.2-vision:90b  
    ollama pull llama3.2-vision:latest 
    ollama pull gemma2:27b gemma:2b 
    ollama pull gemma:latest 
    ollama pull mistral:latest 
    ollama pull codellama:latest 
    ollama pull llama3.2:latest 
```

# Ragging using elastic

Step 1 is to run elastic image:

```md

RUN Elastic:

    docker network create demonet
    mkir ~/data/elastic

    export ESI='-p 9200:9200 docker.elastic.co/elasticsearch/elasticsearch:8.16.1'
    export ESP='-e ELASTICSEARCH_PASSWORD=elastic -e ELASTICSEARCH_USERNAME=elastic'
    export ESS='-e xpack.security.enabled=false -e discovery.type=single-node'
    export ESV='-v ~/data/elastic:/usr/share/elasticsearch/data'
    docker run --rm -it --name es01 --network=demonet ${ESS} ${ESP} ${ESI}

# Now connect using url http://localhost:9200
```

You may want to adjust some parameters

Login to docker as root and install vi

```sh
[ ]
    docker exec -u 0 -it <container es01 /bin/bash
    apt-get update
    apt-get install vim
```


------------------------------------------------------------------------------
# Vision RAG 



Start colpali server:

```
```