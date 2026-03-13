"""
Phase 3, Step 1: LangChain basics and LCEL chains.

What you'll learn:
- How to use LangChain's ChatAnthropic wrapper
- Building chains with LCEL (| pipe operator)
- Prompt templates
- Output parsers (string, JSON, Pydantic)
"""

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatAnthropic(model="claude-sonnet-4-6")


def demo_basic_invoke():
    print("=== 1. Basic Invoke ===")
    messages = [
        SystemMessage(content="You are a helpful assistant who gives concise answers."),
        HumanMessage(content="What is machine learning in one sentence?")
    ]
    response = llm.invoke(messages)
    print(response.content)


def demo_lcel_chain():
    print("\n=== 2. LCEL Chain (prompt | llm | parser) ===")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert in {topic}. Give concise answers."),
        ("human", "{question}")
    ])
    chain = prompt | llm | StrOutputParser()

    result = chain.invoke({
        "topic": "machine learning",
        "question": "What is overfitting?"
    })
    print(result)


def demo_json_output():
    print("\n=== 3. JSON Output Parser ===")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Respond with valid JSON only. No extra text."),
        ("human", "Give me info about {language} as JSON with keys: name, creator, year, main_use")
    ])
    chain = prompt | llm | JsonOutputParser()

    result = chain.invoke({"language": "Python"})
    print(result)
    print(f"\nCreator: {result.get('creator')}")
    print(f"Year: {result.get('year')}")


def demo_pydantic_output():
    print("\n=== 4. Pydantic Structured Output ===")

    class ProgrammingLanguage(BaseModel):
        name: str = Field(description="Language name")
        creator: str = Field(description="Creator's name")
        year: int = Field(description="Year created")
        main_use: str = Field(description="Primary use case")

    structured_llm = llm.with_structured_output(ProgrammingLanguage)
    result = structured_llm.invoke("Tell me about TypeScript")

    print(f"Name: {result.name}")
    print(f"Creator: {result.creator}")
    print(f"Year: {result.year}")
    print(f"Main use: {result.main_use}")


def demo_streaming():
    print("\n=== 5. Streaming ===")
    prompt = ChatPromptTemplate.from_messages([
        ("human", "Write a 3-sentence description of {topic}")
    ])
    chain = prompt | llm | StrOutputParser()

    print("Streaming response: ", end="")
    for chunk in chain.stream({"topic": "LangChain"}):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    demo_basic_invoke()
    demo_lcel_chain()
    demo_json_output()
    demo_pydantic_output()
    demo_streaming()
