from langchain.chains import LLMChain
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
import transformers
from langchain_community.document_loaders import UnstructuredMarkdownLoader, DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
import nest_asyncio
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.runnables import RunnablePassthrough

from model import model, tokenizer

nest_asyncio.apply()

loader = DirectoryLoader('Kubernetes', glob="**/*.md", loader_cls=UnstructuredMarkdownLoader, show_progress=False)
docs = loader.load()

assert len(docs) == 5

text_splitter = CharacterTextSplitter(chunk_size=400, chunk_overlap=0)
chunked_documents = text_splitter.split_documents(docs)
db = FAISS.from_documents(chunked_documents,
                          HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2'))

retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={'k': 4}
)

# print("=================================")
# query = "How to delete a pod?"
# docs = db.similarity_search(query)
# print(docs[3].page_content)

text_generation_pipeline = transformers.pipeline(
    model=model,
    tokenizer=tokenizer,
    task="text-generation",
    temperature=0.2,
    do_sample=True,
    repetition_penalty=1.1,
    return_full_text=True,
    max_new_tokens=400
)


prompt_template = """
### [INST] 
Instruction: Answer the question based on your 
Kubernetes knowledge. Here is context to help:

{context}

### QUESTION:
{question} 

[/INST]
 """

mistral_llm = HuggingFacePipeline(pipeline=text_generation_pipeline)

# Create prompt from prompt template
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=prompt_template,
)

# Create llm chain
llm_chain = LLMChain(llm=mistral_llm, prompt=prompt)

query = "How can I create a dream pod?"

rag_chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | llm_chain
)

r = rag_chain.invoke(query)
print(r)

