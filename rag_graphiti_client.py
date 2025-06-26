
import os

from dotenv import load_dotenv
load_dotenv()
os.environ["NEO4J_URI"]="bolt://localhost:7687"
os.environ["NEO4J_USER"]="neo4j"
os.environ["NEO4J_PASSWORD"]="test1234"
os.environ["DEFAULT_DATABASE"]="neo4j"

# Configure Graphiti
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
from openai import AsyncOpenAI
from logger import logger

# langsmith config
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
os.environ['LANGCHAIN_PROJECT'] = 'Graphiti LangGraph Tutorial'

# OpenAI configuration
os.environ["OPENAI_BASE_URL"] = 'YOUR_OPENAI_BASE_URL'
os.environ["OPENAI_API_KEY"] = 'YOUR_OPENAI_API_KEY'

# Create OpenAI client for LLM
openai_client = AsyncOpenAI()

# Create LLM Config with your Azure deployed model names

# Initialize Graphiti with Azure OpenAI clients
client = Graphiti(
    os.environ["NEO4J_URI"],
    os.environ["NEO4J_USER"],
    os.environ["NEO4J_PASSWORD"],
    llm_client=OpenAIClient(
        config=LLMConfig(
            small_model="YOUR_TEXT_GENERATE_MODEL_NAME",
            model="YOUR_TEXT_GENERATE_MODEL_NAME",
            max_tokens=12288,
        ),
        client=openai_client,
        max_tokens=12288
    ),
    embedder=OpenAIEmbedder(
        config=OpenAIEmbedderConfig(
            embedding_model="YOUR_TEXT_EMBEDDING_MODEL_NAME"  # Use your Azure deployed embedding model name
        ),
        client=openai_client,
    ),
    # Optional: Configure the OpenAI cross encoder with Azure OpenAI
    # cross_encoder=OpenAIRerankerClient(
    #     config=LLMConfig(
    #         model="",
    #         max_tokens=12288,
    #     ),
    #     client=openai_client,
    # ),
)

from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model_name="YOUR_TEXT_GENERATE_MODEL_NAME",
    verbose=True,
    streaming=False,
    temperature=0,
    max_tokens=12288,
    max_retries = 3,
)