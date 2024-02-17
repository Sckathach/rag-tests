from langchain_community.llms import HuggingFacePipeline
from langchain_core.runnables import RunnablePassthrough
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import transformers
import nest_asyncio

from model import model, tokenizer
from rag import db, retriever

nest_asyncio.apply()

query = "How to delete a pod?"
docs = db.similarity_search(query)
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

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=prompt_template,
)

llm_chain = LLMChain(llm=mistral_llm, prompt=prompt)

rag_chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | llm_chain
)

query = "How can I create a dream pod?"
r = rag_chain.invoke(query)
# print(r)
