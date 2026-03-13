"""
Phase 5, Step 1: Basic RAG (Retrieval Augmented Generation) pipeline.

What you'll learn:
- Chunking documents
- Creating embeddings with sentence-transformers
- Storing vectors in ChromaDB
- Building a retrieval chain
- Grounding AI answers in your own documents
"""

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


# ============================================================
# INDEXING PHASE (run once to build the knowledge base)
# ============================================================

# 1. Your documents — in a real app you'd load PDFs, web pages, etc.
documents = [
    Document(
        page_content="""LangGraph is a library for building stateful, multi-actor applications with LLMs.
        It extends LangChain to support cyclic computation graphs. This makes it ideal for building agents
        that need to loop, branch, and maintain state across multiple steps. LangGraph uses a node/edge
        architecture where nodes are Python functions and edges define the flow between them.""",
        metadata={"source": "langgraph_docs", "topic": "langgraph"}
    ),
    Document(
        page_content="""RAG stands for Retrieval Augmented Generation. It is a technique that combines
        information retrieval with text generation. Instead of relying solely on what the model learned
        during training, RAG retrieves relevant documents at query time and includes them as context.
        This allows the model to answer questions about private or recent information.""",
        metadata={"source": "ai_concepts", "topic": "rag"}
    ),
    Document(
        page_content="""Claude is an AI assistant made by Anthropic. It is designed to be helpful,
        harmless, and honest. Claude can assist with coding, writing, analysis, math, and many other
        tasks. The latest models include Claude Sonnet 4.6 and Claude Opus 4.6. Claude supports
        function/tool calling which enables building AI agents.""",
        metadata={"source": "anthropic_docs", "topic": "claude"}
    ),
    Document(
        page_content="""Vector databases store numerical representations (embeddings) of text.
        When you search a vector database, it finds the most semantically similar entries
        using cosine similarity or dot product distance. Popular vector databases include
        ChromaDB (local), Pinecone (cloud), Weaviate, and pgvector (PostgreSQL extension).""",
        metadata={"source": "ai_concepts", "topic": "vector_databases"}
    ),
    Document(
        page_content="""LangChain is an open-source framework for building LLM-powered applications.
        It provides abstractions for prompts, chains, agents, memory, and tools. The LangChain
        Expression Language (LCEL) uses the pipe operator to compose components declaratively.
        LangChain supports many LLM providers including Anthropic, OpenAI, and open-source models.""",
        metadata={"source": "langchain_docs", "topic": "langchain"}
    ),
]

# 2. Split documents into smaller chunks
# chunk_size: max characters per chunk
# chunk_overlap: overlap between chunks to avoid cutting context
splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
chunks = splitter.split_documents(documents)
print(f"Split {len(documents)} documents into {len(chunks)} chunks")

# 3. Create embeddings (converts text to vectors)
# all-MiniLM-L6-v2 is a small, fast model — good for local dev
# Downloads automatically on first run (~90MB)
print("Loading embedding model (downloads on first run)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 4. Store in ChromaDB (local, in-memory for this demo)
vectorstore = Chroma.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # Return top 3 most relevant chunks
)
print("Vector store built.\n")


# ============================================================
# QUERY PHASE (runs on every user question)
# ============================================================

llm = ChatAnthropic(model="claude-sonnet-4-6")

rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant. Answer the user's question using ONLY the
provided context. If the answer is not in the context, say "I don't have information about that."

Context:
{context}"""),
    ("human", "{question}")
])


def format_docs(docs: list[Document]) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


# Build the RAG chain
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough()
    }
    | rag_prompt
    | llm
    | StrOutputParser()
)


def ask(question: str):
    print(f"Q: {question}")

    # Also show what was retrieved
    docs = retriever.invoke(question)
    print(f"Retrieved {len(docs)} chunks:")
    for i, doc in enumerate(docs, 1):
        print(f"  [{i}] {doc.page_content[:80]}...")

    answer = rag_chain.invoke(question)
    print(f"\nA: {answer}\n")
    print("=" * 60)


if __name__ == "__main__":
    ask("What is LangGraph and why would I use it?")
    ask("How does RAG work?")
    ask("What vector databases can I use?")
    ask("Who made Claude?")
    ask("What is the capital of France?")  # Not in our docs — should say "I don't know"
