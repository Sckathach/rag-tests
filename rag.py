from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter, Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import nest_asyncio
from typing import List, Dict, Any

nest_asyncio.apply()

loader = DirectoryLoader('Kubernetes', glob="**/*.md", loader_cls=UnstructuredMarkdownLoader, show_progress=False)
docs = loader.load()

assert len(docs) == 5
chunk_size = 300
chunk_overlap = 50

text_splitter = CharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=chunk_overlap,
)
chunked_documents = text_splitter.split_documents(docs)
# db = FAISS.from_documents(chunked_documents,
#                           HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2'))
#
# retriever = db.as_retriever(
#     search_type="similarity",
#     search_kwargs={'k': 4}
# )


class EmbedChunks:
    def __init__(self, model_name: str):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name
        )

    def __call__(self, batch: List[Document]) -> List[Dict[str, Any]]:
        embeddings = self.embedding_model.embed_documents([x.page_content for x in batch])
        return [
            {
                "text": x.page_content,
                "source": x.metadata["source"],
                "embeddings": y
            } for x, y in zip(batch, embeddings)
        ]


embedder = EmbedChunks(model_name="sentence-transformers/all-mpnet-base-v2")
r = embedder(chunked_documents)
print(r[:10])
