"""
Phase 5, Step 2: Agentic RAG with LangGraph.

What you'll learn:
- Combining RAG with LangGraph for smarter retrieval
- Grading document relevance before answering
- Falling back gracefully when context is insufficient
- Building a graph that can retrieve, evaluate, and generate
"""

import operator
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

load_dotenv()

# ============================================================
# Build vector store (same as 01_basic_rag.py)
# ============================================================

docs = [
    Document(page_content="LangGraph is a library for building stateful agent workflows as graphs."),
    Document(page_content="RAG stands for Retrieval Augmented Generation. It grounds LLM answers in real documents."),
    Document(page_content="Claude is an AI assistant made by Anthropic. It supports tool use and is available via API."),
    Document(page_content="ChromaDB is a local vector database used for storing and searching embeddings."),
]

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
chunks = splitter.split_documents(docs)
print("Loading embeddings...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
print("Ready.\n")

llm = ChatAnthropic(model="claude-sonnet-4-6")


# ============================================================
# State
# ============================================================

class RAGState(TypedDict):
    question: str
    documents: list[Document]
    answer: str
    relevant: bool


# ============================================================
# Grader — checks if retrieved docs actually answer the question
# ============================================================

class RelevanceScore(BaseModel):
    relevant: bool = Field(description="True if the documents contain an answer to the question")
    reason: str = Field(description="One sentence explanation")


grader_llm = llm.with_structured_output(RelevanceScore)

grader_prompt = ChatPromptTemplate.from_messages([
    ("system", "You assess whether retrieved documents contain enough info to answer a question."),
    ("human", "Question: {question}\n\nDocuments:\n{documents}\n\nAre these documents relevant?")
])

grader_chain = grader_prompt | grader_llm


# ============================================================
# Generator — produces the final answer from context
# ============================================================

generate_prompt = ChatPromptTemplate.from_messages([
    ("system", """Answer the question using ONLY the context below.
If the context doesn't contain the answer, say so clearly.

Context:
{context}"""),
    ("human", "{question}")
])

generate_chain = generate_prompt | llm | StrOutputParser()


# ============================================================
# Graph Nodes
# ============================================================

def retrieve_node(state: RAGState) -> dict:
    """Retrieve documents from the vector store."""
    print(f"[retrieve] Searching for: {state['question']}")
    docs = retriever.invoke(state["question"])
    print(f"[retrieve] Found {len(docs)} chunks")
    return {"documents": docs}


def grade_node(state: RAGState) -> dict:
    """Grade whether retrieved documents are relevant to the question."""
    context = "\n\n".join(doc.page_content for doc in state["documents"])
    score = grader_chain.invoke({
        "question": state["question"],
        "documents": context
    })
    print(f"[grade] Relevant: {score.relevant} — {score.reason}")
    return {"relevant": score.relevant}


def generate_node(state: RAGState) -> dict:
    """Generate an answer from the retrieved documents."""
    context = "\n\n".join(doc.page_content for doc in state["documents"])
    answer = generate_chain.invoke({
        "question": state["question"],
        "context": context
    })
    return {"answer": answer}


def fallback_node(state: RAGState) -> dict:
    """Return a fallback answer when documents aren't relevant."""
    return {"answer": "I don't have relevant information in my knowledge base to answer that question."}


# ============================================================
# Routing
# ============================================================

def route_after_grade(state: RAGState) -> str:
    return "generate" if state["relevant"] else "fallback"


# ============================================================
# Build Graph
# ============================================================

graph = StateGraph(RAGState)

graph.add_node("retrieve", retrieve_node)
graph.add_node("grade", grade_node)
graph.add_node("generate", generate_node)
graph.add_node("fallback", fallback_node)

graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "grade")
graph.add_conditional_edges(
    "grade",
    route_after_grade,
    {"generate": "generate", "fallback": "fallback"}
)
graph.add_edge("generate", END)
graph.add_edge("fallback", END)

rag_app = graph.compile()


def ask(question: str):
    print(f"\nQuestion: {question}")
    print("-" * 50)
    result = rag_app.invoke({"question": question, "documents": [], "answer": "", "relevant": False})
    print(f"\nAnswer: {result['answer']}")
    print("=" * 60)


if __name__ == "__main__":
    ask("What is LangGraph?")
    ask("What is RAG?")
    ask("What is the weather like today?")  # Not in knowledge base
