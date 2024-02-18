from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter, Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List, Dict, Any, Union
import nest_asyncio
import psycopg2

from db_utils import create_db_connection

nest_asyncio.apply()


class EmbedChunks:
    def __init__(self, model_name: str):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name
        )

    def __call__(self, batch: List[Document]) -> List[Dict[str, Union[str, List[float]]]]:
        embeddings = self.embedding_model.embed_documents([x.page_content for x in batch])
        return [
            {
                "text": x.page_content,
                "source": x.metadata["source"],
                "embedding": y
            } for x, y in zip(batch, embeddings)
        ]

    def single(self, text: str) -> List[float]:
        return self.embedding_model.embed_documents([text])[0]


embedder = EmbedChunks(model_name="sentence-transformers/all-mpnet-base-v2")


def create_chunked_docs():
    chunk_size = 300
    chunk_overlap = 50

    loader = DirectoryLoader('Kubernetes', glob="**/*.md", loader_cls=UnstructuredMarkdownLoader,
                             show_progress=False)
    docs = loader.load()

    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunked_documents = text_splitter.split_documents(docs)
    return chunked_documents


def create_vector_database(chunked_documents):
    r = embedder(chunked_documents)
    connection = create_db_connection()
    cursor = connection.cursor()
    try:
        for x in r:
            cursor.execute(
                "INSERT INTO embeddings (embedding, text, metadata) VALUES (%s, %s, %s)",
                (x["embedding"], x["text"], x["source"])
            )
        connection.commit()
    except (Exception, psycopg2.Error) as error:
        print(f'Error while writing to DB: {error}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def retrieve(query: str) -> List[Dict[str, Any]]:
    embed = embedder.single(query)
    connection = create_db_connection()
    cursor = connection.cursor()
    response = []
    try:
        cursor.execute(f"""
            SELECT text, 1 - (embedding <=> '{embed}') AS cosine_similarity
            FROM embeddings
            ORDER BY cosine_similarity desc
            LIMIT 3
        """)
        for r in cursor.fetchall():
            response.append({"text": r[0], "similarity": r[1]})
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
        return response


def retrieve_to_string(query: str) -> str:
    r = retrieve(query)
    response = ""
    for x in r:
        response += x["text"] + "\n"
    return response


# create_vector_database(create_chunked_docs())
# print(retrieve("How to create a dream pod?"))
