from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter, Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import nest_asyncio
from typing import List, Dict, Any, Union
from db_utils import create_db_connection
import psycopg2

nest_asyncio.apply()


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


# query = "How to create dream pods?"
# embed = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2").embed_documents([query])[0]
#
# connection = create_db_connection()
# cursor = connection.cursor()
# try:
#     cursor.execute(f"""
#         SELECT text, 1 - (embedding <=> '{embed}') AS cosine_similarity
#         FROM embeddings
#         ORDER BY cosine_similarity desc
#         LIMIT 3
#     """)
#     for r in cursor.fetchall():
#         print(f"Text: {r[0]}; Similarity: {r[1]}")
# except Exception as e:
#     print("Error: ", e)
# finally:
#     cursor.close()
#     connection.close()

embedder = EmbedChunks(model_name="sentence-transformers/all-mpnet-base-v2")


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


print(retrieve("How to create a dream pod?"))
