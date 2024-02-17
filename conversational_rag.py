from langchain.memory import ConversationBufferMemory
from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline
from model import model, tokenizer
from langchain.prompts.prompt import PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain.schema import format_document
from langchain_core.messages import AIMessage, HumanMessage, get_buffer_string
from langchain_core.runnables import RunnableParallel
from operator import itemgetter
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from rag import retriever

standalone_query_generation_pipeline = pipeline(
    model=model,
    tokenizer=tokenizer,
    task="text-generation",
    # TODO: is do_sample useful?
    do_sample=True,
    # TODO: is it possible to set the temperature to 0 somehow? ValueError: `temperature` (=0.0) has to be a strictly
    #  positive float, otherwise your next token scores will be invalid. If you're looking for greedy decoding
    #  strategies, set `do_sample=False`.
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
Given the following conversation and a follow up question, 
rephrase the follow up question to be a standalone question, in its original language, 
that can be used to query a FAISS index. This query will be used to retrieve documents with additional context.

Let me share a couple examples.

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

# Instantiate ConversationBufferMemory
# memory = ConversationBufferMemory(
#     return_messages=True, output_key="answer", input_key="question"
# )
# # First, load the memory to access chat history
# loaded_memory = RunnablePassthrough.assign(
#     chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
# )
# Define the standalone_question step to process the question and chat history
# standalone_question = {
#     "standalone_question": {
#                                "question": lambda x: x["question"],
#                                "chat_history": lambda x: get_buffer_string(x["chat_history"]),
#                            }
#                            | STANDALONE_QUESTION_PROMPT,
# }
# # Finally, output the result of the CONDENSE_QUESTION_PROMPT
# output_prompt = {
#     "standalone_question_prompt_result": itemgetter("standalone_question"),
# }
# Combine the steps into a final chain
# standalone_query_generation_prompt = loaded_memory | standalone_question | output_prompt

# inputs = {"question": "What is a dream pod?"}
# memory.save_context(inputs, {"answer": "A dream pod is a special Kubernetes pod."})

# r = standalone_query_generation_prompt.invoke(inputs)['standalone_question_prompt_result']

# standalone_query_generation_chain = (
#         loaded_memory
#         | {
#             "question": lambda x: x["question"],
#             "chat_history": lambda x: get_buffer_string(x["chat_history"]),
#         }
#         | STANDALONE_QUESTION_PROMPT
#         | standalone_query_generation_llm
# )
#
# inputs = {"question": "How can I create one?"}
# r = standalone_query_generation_chain.invoke(inputs)

template = """
[INST] 
Answer the question based only on the following context:
{context}

Question: {standalone_question}
[/INST] 
"""

ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")


def _combine_documents(
        docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


# First we add a step to load memory
# This adds a "memory" key to the input object
loaded_memory = RunnablePassthrough.assign(
    chat_history=RunnableLambda(memory.load_memory_variables) | itemgetter("history"),
)

# Now we calculate the standalone question
standalone_question = {
    "standalone_question": {
                               "question": lambda x: x["question"],
                               "chat_history": lambda x: get_buffer_string(x["chat_history"]),
                           }
                           | CONDENSE_QUESTION_PROMPT
                           | standalone_query_generation_llm,
}
# Now we retrieve the documents
retrieved_documents = {
    "docs": itemgetter("standalone_question") | retriever,
    "standalone_question": lambda x: x["standalone_question"],
}
# Now we construct the inputs for the final prompt
final_inputs = {
    "context": lambda x: _combine_documents(x["docs"]),
    "standalone_question": itemgetter("standalone_question"),
}
# And finally, we do the part that returns the answers
answer = {
    "answer": final_inputs | ANSWER_PROMPT | response_generation_llm,
    "standalone_question": itemgetter("standalone_question"),
    "context": final_inputs["context"]
}
# And now we put it all together!
final_chain = loaded_memory | standalone_question | retrieved_documents | answer
