from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from langchain.schema import format_document
from langchain_core.messages import get_buffer_string
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate

from operator import itemgetter

from rag import retriever
from model import model, tokenizer

standalone_query_generation_pipeline = pipeline(
    model=model,
    tokenizer=tokenizer,
    task="text-generation",
    do_sample=True,
    temperature=0.001,
    repetition_penalty=1.1,
    return_full_text=True,
    max_new_tokens=1000,
)
standalone_query_generation_llm = HuggingFacePipeline(pipeline=standalone_query_generation_pipeline)

response_generation_pipeline = pipeline(
    model=model,
    tokenizer=tokenizer,
    task="text-generation",
    do_sample=True,
    temperature=0.2,
    repetition_penalty=1.1,
    return_full_text=True,
    max_new_tokens=1000,
)
response_generation_llm = HuggingFacePipeline(pipeline=response_generation_pipeline)

_template = """
[INST] 
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language, that can be used to query a FAISS index. This query will be used to retrieve documents with additional context. 

Let me share a couple examples that will be important. 

If you do not see any chat history, you MUST return the "Follow Up Input" as is:

```
Chat History:

Follow Up Input: How is Lawrence doing?
Standalone Question:
How is Lawrence doing?
```

If this is the second question onwards, you should properly rephrase the question like this:

```
Chat History:
Human: How is Lawrence doing?
AI: 
Lawrence is injured and out for the season.

Follow Up Input: What was his injury?
Standalone Question:
What was Lawrence's injury?
```

Now, with those examples, here is the actual chat history and input question.

Chat History:
{chat_history}

Follow Up Input: {question}
Standalone question:
[your response here]
[/INST] 
"""

CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

template = """
[INST] 
Answer the question based only on the following context:
{context}

Question: {question}
[/INST] 
"""
ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")


def _combine_documents(docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


memory = ConversationBufferMemory(
    return_messages=True, output_key="answer", input_key="question"
)

loaded_memory = RunnablePassthrough.assign(
    chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
)

standalone_question = {
    "standalone_question": {
                               "question": lambda x: x["question"],
                               "chat_history": lambda x: get_buffer_string(x["chat_history"]),
                           }
                           | CONDENSE_QUESTION_PROMPT
                           | standalone_query_generation_llm,
}
retrieved_documents = {
    "docs": itemgetter("standalone_question") | retriever,
    "question": lambda x: x["standalone_question"],
}
final_inputs = {
    "context": lambda x: _combine_documents(x["docs"]),
    "question": itemgetter("question"),
}
answer = {
    "answer": final_inputs | ANSWER_PROMPT | response_generation_llm,
    "question": itemgetter("question"),
    "context": final_inputs["context"]
}
final_chain = loaded_memory | standalone_question | retrieved_documents | answer


def call_conversational_rag(question, chain, memory):
    inputs = {"question": question}
    result = chain.invoke(inputs)
    memory.save_context(inputs, {"answer": result["answer"]})
    return result


q1 = "What is a dream pod?"
r1 = call_conversational_rag(q1, final_chain, memory)["answer"]

q2 = "How to create one?"
r2 = call_conversational_rag(q2, final_chain, memory)["answer"]

q3 = "What did I asked for in the first place?"
r3 = call_conversational_rag(q3, final_chain, memory)["answer"]

print("\n\n\n\n\n=================================================\n")
print("Sckathach: ", q1)
print("Merlin:", r1)
print("Sckathach: ", q2)
print("Merlin:", r2)
print("Sckathach: ", q3)
print("Merlin:", r3)
