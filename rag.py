from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import nest_asyncio

nest_asyncio.apply()

loader = DirectoryLoader('Kubernetes', glob="**/*.md", loader_cls=UnstructuredMarkdownLoader, show_progress=False)
docs = loader.load()

assert len(docs) == 5

text_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=0)
chunked_documents = text_splitter.split_documents(docs)
db = FAISS.from_documents(chunked_documents,
                          HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2'))

retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={'k': 4}
)
