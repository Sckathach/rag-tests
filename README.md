# RAG Tests

## Resources used
- Simple RAG: https://medium.com/@thakermadhav/build-your-own-rag-with-mistral-7b-and-langchain-97d0c92fa146
- Conversational RAG: https://github.com/madhavthaker1/llm/blob/main/rag/conversational_rag.ipynb
- LangChain doc: https://python.langchain.com/docs/modules/data_connection/document_loaders/file_directory
- Anyscale: https://www.anyscale.com/blog/a-comprehensive-guide-for-building-rag-based-llm-applications-part-1

## Deployment using Ray?
- Ray on Kubernetes: https://docs.ray.io/en/latest/cluster/kubernetes/index.html

## Troubleshooting
- CUDA out of memory error &rarr; reduced chunk size from 600 to 300 and added 
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` variable when launching python scripts. 
