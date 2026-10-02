import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing")

api_key = api_key.strip()

llm = ChatGroq(
    api_key=api_key,
    model="openai/gpt-oss-120b"
)