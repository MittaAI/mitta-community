# RAG Indexing and Search Pipeline
This pipeline implements a RAG (retrieval augmented generation) indexing and querying pipeline system. Use it search texts for matches for prompt assembly.

## Video Guide
Watch the video guide before beginning installation.

[![RAG](https://img.youtube.com/vi/nlnFbU88sdg/0.jpg)](https://www.youtube.com/watch?v=nlnFbU88sdg)

## Install
Add the pipelines to [MittaAI](https://mitta.ai) from the `pipelines` page. 

## Use
Upload a file to the pipeline from the indexing pipeline detail page. Wait until the pipeline has completed before querying it.

If you have issues configuring the overlaps and chunk sizes for your documents, pop into [Discord](https://discord.com/invite/SxwcVGQ8j9).

### Query the Document
You can query the document by submitting a task to the pipeline's endpoint:

```
curl -X POST "https://mitta.ai/pipeline/aejsLI8x3oS1t/task?token=<token>" \
-H "Content-Type: application/json" \
-d '{"query": "Tell me more about this document."}'
```

### Sample Output
```
"Winnie the Pooh, also known as Pooh Bear, is a fictional anthropomorphic teddy bear created by English author A. A. Milne. The character first appeared in the book 'Winnie-the-Pooh' (1926), followed by 'The House at Pooh Corner' (1928). The stories of Pooh Bear are set in Ashdown Forest, East Sussex, England. Pooh is a nau00efve and slow-witted yet friendly and thoughtful bear who lives in the Hundred Acre Wood.
```
