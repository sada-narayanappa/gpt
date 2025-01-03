# Implementing Vision model and use it as RAG system

This describes how to implement Vision RAG system some important considerations.
There are several parameters that are crucial in implementing RAG system. One small deviation will 
make the results so widely out of norm and it could be devastating to fix the bugs.

Before speaking of the parameters and careful consideration, lets review the RAG pipeline.

| FIRST Stage (docs)          | Second stage (Q = Query)                  | 
| -----------------           | -----------------------------------       | 
| INDEX Documents             |   (a) Search and create context for Q     |
|                             |   (b) Call LLM with the context and query | 


### Considerations

Indexing

* Choice of model to create embedding 
* if PDF, create each page image with 400  (image = page.to_image(resolution=400))
    => experiement with higher resolutions.
* 