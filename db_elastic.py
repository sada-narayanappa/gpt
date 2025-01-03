#!/usr/bin/env python 

import os, sys, logging, argparse, glob
sys.path.append(os.path.expanduser("~/.django") )
sys.path.append(os.path.expanduser("gpt") )

from importlib import metadata
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_elasticsearch import (
    BM25Strategy,
    DenseVectorStrategy,
    ElasticsearchStore,
)

from elasticsearch import Elasticsearch
from mangorest.mango import webapi
from pdf_parser_tools import pdf_parser
from dataframe_tools import merge_records,metadata_chunks,chunk_dict_to_list, chunks_to_doc_obj

logger = logging.getLogger( "gpt" )

# You can set these in your ~/.django/my_config

ES_URL, ES_USER, ES_PW  = "http://localhost:9200", "elastic", "elastic"
ES_CNX= dict(es_url= ES_URL, es_user= ES_USER, es_password=ES_PW)

if (os.path.exists(os.path.expanduser("~/.django/my_config.py"))):
    import my_config
    try:
        from my_config import ES_URL, ES_USER, ES_PW
    except:
        pass


_ES_STARTEGIES = {
    "hnsw":     DenseVectorStrategy(), 
    "bm25":     BM25Strategy(),
    "hybrid":   DenseVectorStrategy(hybrid=True, rrf=False),
    "sparse":   None,
    "exact":    None,
}
# ---------------------------------------------------------------------------------------
def esDeleteIndex(index):
    esclient = Elasticsearch(ES_URL, basic_auth = (ES_USER, ES_PW))
    esclient.info()
    try:
        esclient.indices.delete(index=index)
    except:
        pass
# ---------------------------------------------------------------------------------------
def esCreateIndex(index):
    esclient = Elasticsearch(ES_URL, basic_auth = (ES_USER, ES_PW))
    esclient.indices.create(index=index)
# ---------------------------------------------------------------------------------------
def getEmbedding(model="llama3.2",base_url = "http://127.0.0.1:11434/"):
    e = OllamaEmbeddings( model = model, base_url =base_url )
    return e
# ---------------------------------------------------------------------------------------
def add_to_es( docs: list[Document], es_cnx: dict, index: str, embed, strategy= "hnsw" ):
    strat = _ES_STARTEGIES[strategy]
    vectorstore = None
    for i in range(0, len(docs), 20000):
        vectorstore = ElasticsearchStore.from_documents(
            documents=docs[i : min(i + 20000, len(docs))],
            embedding=embed,
            **es_cnx,
            index_name=index,
            bulk_kwargs={
                "chunk_size": 100,
            },
            strategy=strat,
        )
    return vectorstore

# ---------------------------------------------------------------------------------------
def es_retriever( es_cnx: dict, index: str, embed, strategy="hnsw", k= 10 ):
    strat = _ES_STARTEGIES[strategy]

    v = ElasticsearchStore( **es_cnx, embedding=embed, index_name=index, strategy=strat)
    return v.as_retriever(search_kwargs={"k": k})

def esVectorSearch( retreiver, q, k=10):
        ret = retreiver.as_retriever(search_kwargs={"k": k}).invoke(q)
        
        h = {r.page_content:r for r in ret}
        if len(h) != len(ret):
            ret = [v for v in h.values()]
            
        return ret



@webapi("/gpt/esSearchIndex/")
def esSearchIndex(request, index_name, query, model="llama3.2", user="", es_url="", 
                    es_user="", es_pass="", k=10, rank=1, **kwargs):

    print(f""" 
        {locals()}
    """)
        
    if (not es_url):
        es = dict(es_url= ES_URL, es_user=ES_USER, es_password=ES_PW)
    else:
        es = dict(es_url= es_url, es_user=es_user, es_password=es_pass)

    #model = "llama3.2" #lets force the embedding for now
    embed = getEmbedding(model=model) 

    
    if ( rank):
        v = es_retriever(es, index=index_name, embed=embed, k=k*2)
        docs = v.invoke(query)
        if (len(docs)):
            ranked = rerank( query, docs)
            docs = [Document(page_content=r['text'], metadata=r['metadata']) for r in ranked[0:k]]
    else:
        v = es_retriever(es, index=index_name, embed=embed, k=k)
        docs = v.invoke(query)

    h = {r.page_content: r for r in docs}
    if len(h) != len(docs):
        docs = [v for v in h.values()]
    
    ret = []
    for d in docs:
        ret.append(dict(page_content=d.page_content, metadata=d.metadata))
    return ret



def esTextSearch(q, k=10, index="test", url = ES_URL, user=ES_USER, pw= ES_PW):
    esclient = Elasticsearch(url, basic_auth = (user, pw))
    res = esclient.search(index=index,  q=q, size=k)

    ret = []
    for i,r in enumerate(res['hits']['hits']):
        pc = r['_source']['text']
        mt = r['_source']['metadata']
        ret.append(Document(page_content = pc, metadata=mt))
        #print(i, " ==>", )
    return ret

# ---------------------------------------------------------------------------------------
def rerank(q, ret):
    from flashrank import (Ranker, RerankRequest,)

    ranker = Ranker("ms-marco-MiniLM-L-12-v2", os.path.expanduser("~/.cache/RERANKER/"))
    rerankrequest = RerankRequest(
        query=q, passages=[{"text": d.page_content, "metadata": d.metadata} for d in ret]
    )
    reranked = ranker.rerank(rerankrequest)
    return reranked

# ---------------------------------------------------------------------------------------
def getchunksFromPDF(filename):
    filename = os.path.expanduser(filename)
    
    record = pdf_parser(filename)
    # Seems like there is not data excepts figures and tables in the pdf
    if ( not record ):
        logger.info("Hmmmm not records found in PDF file!")
        return [] 

    merged = merge_records(record)

    docName = os.path.basename(filename)
    chunk_dict = metadata_chunks(merged,docName)
    chunks = chunk_dict_to_list(chunk_dict)
    docs = chunks_to_doc_obj(chunks, docName )
    return docs
# ---------------------------------------------------------------------------------------
# This is standing by itself - should be called by indexFromFolder
# can be multi tasked 
def loadES( model="llama3.2", index="", filename = '~/data/gpt/test-files/HS4_SGS1_V1S7.pdf',
           es_url=ES_URL , es_user=ES_USER, es_password=ES_PW ):
    
    docs = []
    if ( filename.endswith(".pdf")):
        docs = getchunksFromPDF(filename)
    else:
        logger.info("Indexing only PDF files now!! :)")

    if (not docs):
        return docs
    embed= getEmbedding(model)
    es = dict(es_url=es_url , es_user=es_user, es_password=es_password)
    v = add_to_es(docs, es, index=index, embed=embed)

    return docs

# ---------------------------------------------------------------------------------------
def indexFromFolderOLD(folder="", force=0, index="test", url=ES_URL, user=ES_USER, pw= ES_PW, model="llama3.2"):
    import extract_text

    folder = os.path.expanduser(folder) + "/*"
    files = [f for f in glob.glob(folder, recursive=0) if os.path.isfile(f)]

    embed= getEmbedding(model)
    es = dict(es_url=url , es_user=user, es_password=pw)

    for f in files:
        marker = f".{f}.{index}.indexed"
        if f.endswith(".indexed") or (os.path.exists( marker) and not force):
            continue;

        logger.info(f"Indexing {f}")        
        try:
            docs = extract_text.getChunks(f)
            v = add_to_es(docs, es, index=index, embed=embed)
            open(marker, "w").write("")
        except Exception as e:
            logger.error(f"{f} failed to index")
            pass

    return files

# ---------------------------------------------------------------------------------------
def indexFromFolder(folder="", force=0, index="test", url=ES_URL, user=ES_USER, pw= ES_PW, model="llama3.2"):
    folder = os.path.expanduser(folder) + "/*"
    files = [f for f in glob.glob(folder, recursive=0) if os.path.isfile(f)]

    embed= getEmbedding(model)
    es = dict(es_url=url , es_user=user, es_password=pw)

    logger.info(f"Indexing files from {folder}: found {len(files)} files.")        

    iFiles = []
    for f in files:
        bn = os.path.basename(f)
        dn = os.path.dirname(f)
        marker = f"{dn}/.{bn}.{index}.indexed"

        if f.endswith(".indexed") or (os.path.exists( marker) and not force):
            continue;

        logger.info(f"Indexing {f}")        
        try:
            loadES(model, index, f, url, user, pw)
            open(marker, "w").write("")
            iFiles.append(f)
        except Exception as e:
            logger.error(f"{f} failed to index {e}")
            pass

    return iFiles


#-----------------------------------------------------------------------------------
sysargs=None
def addargs(argv=sys.argv):
    global sysargs
    p = argparse.ArgumentParser(f"{os.path.basename(argv[0])}:")
    p.add_argument('-p', '--path',   type=str, required=True, help="where files are located to index")
    p.add_argument('-i', '--index',  type=str, required=True, help="Elastic Search index")
    p.add_argument('-m', '--model',  type=str, required=False, default="all-minilm:L6-v2", help="embedding model")
    p.add_argument('-e', '--es_url', type=str, required=False, default=ES_URL,  help="elastic URL")
    p.add_argument('-u', '--es_user',type=str, required=False, default=ES_USER, help="elastic user")
    p.add_argument('-w', '--es_pass',type=str, required=False, default=ES_PW,   help="elastic password")
    p.add_argument('-f', '--force',  required=False, default=False, action='store_true', help="force")

    sysargs=p.parse_args(argv[1:])
    return sysargs

from colabexts import utils as colabexts_utils
if __name__ == '__main__' and not colabexts_utils.inJupyter():
    a = addargs()
    logger.info(f"Indexing  {sysargs}")

    indexFromFolder(folder=a.path, force=a.force, index=a.index, url=a.es_url, 
                        user=a.es_user, pw= a.es_pass, model=a.model)

#    indexFromFolder(sys.argv[1])
# index, model = "test2", "all-minilm:L6-v2"
# index, model = "test3", "llama3.2:latest"

# esDeleteIndex(index)
# esCreateIndex(index)

# loadES(model, index);
