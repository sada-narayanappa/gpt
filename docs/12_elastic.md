# Setup Elastic search as docker

>
```
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.18.1
```

## RUN Elastic:

```

docker network create demonet
mkdir ~/data/elastic # on linux mkdir /disk01/elastic

export ESI='-p 9200:9200 -p 9300:9300 docker.elastic.co/elasticsearch/elasticsearch:8.18.1'
export ESP='-e ELASTICSEARCH_PASSWORD=elastic -e ELASTICSEARCH_USERNAME=elastic'
export ESS='-e xpack.security.enabled=false -e "discovery.type=single-node" -e "network.host=0.0.0.0"'

#export ESV='-v ~/data/elastic:/usr/share/elasticsearch/data'
#docker run --rm -it --name es01 --network=demonet ${ESS} ${ESV} ${ESP} ${ESI} 

#for LINUX
docker volme create es
export ESV='--mount source=es,target=/usr/share/elasticsearch/data,type=volume'
docker run --rm -itd --name es01 --network=demonet ${ESS} ${ESV} ${ESP} ${ESI} 

```
