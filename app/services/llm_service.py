import os
import json
from typing import TypedDict, List
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langgraph.graph import StateGraph, END
from pinecone import Pinecone, ServerlessSpec
from ..config import get_settings

settings = get_settings()

# 1. Initialize Components
# Use HF Inference API to save memory (runs on HF servers, not locally)
embeddings = HuggingFaceEndpointEmbeddings(
    huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN,
    model="sentence-transformers/all-MiniLM-L6-v2"
)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=settings.GROQ_API_KEY,
    temperature=0
)

# Initialize Pinecone
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Ensure Index Exists (Simple check for demo purposes)
index_name = settings.PINECONE_INDEX_NAME
if index_name not in [i.name for i in pc.list_indexes()]:
    try:
        pc.create_index(
            name=index_name,
            dimension=384, # Dimension for all-MiniLM-L6-v2
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    except Exception as e:
        print(f"Could not create index (might already exist or permission issue): {e}")

vectorstore = PineconeVectorStore(
    index_name=index_name, 
    embedding=embeddings, 
    pinecone_api_key=settings.PINECONE_API_KEY
)

# Seeding is now handled by seed_db.py

# 2. Define Graph State
class AgentState(TypedDict):
    user_message: str
    context: List[Document]
    response: dict

# 3. Define Nodes
def retrieve(state: AgentState):
    """Retrieve relevant documents"""
    print(f"Retrieving for: {state['user_message']}")
    try:
        docs = vectorstore.similarity_search(state['user_message'], k=3)
        print(f"Retrieved {len(docs)} documents.")
        return {"context": docs}
    except Exception as e:
        print(f"Error in retrieval: {e}")
        return {"context": []}

def generate(state: AgentState):
    """Generate response using LLM"""
    print("Generating response...")
    context_text = "\n\n".join([doc.page_content for doc in state['context']])
    
    system_prompt = """You are an expert customer support AI. 
    Analyze the inquiry using the provided Context.
    
    Context:
    {context}
    
    Output JSON with keys: "category", "urgency", "reply".
    1. Category: Refund, Order Status, Complaint, Product Question, Technical Issue, Other.
    2. Urgency: Low, Medium, High.
    3. Reply: Professional, empathetic, specific.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{user_message}")
    ])
    
    # Enforce JSON mode via Groq/LangChain if supported, or just prompt engineering
    # ChatGroq supports json_mode in bind_tools or similar, but simple prompting works well with Llama 3
    chain = prompt | llm.with_structured_output(method="json_mode") 
    # Note: with_structured_output is newer, if it fails we fall back to parsing
    
    try:
        # We'll try to use the json mode of the model
        print("Sending request to Groq...")
        response = llm.invoke(
            prompt.format_messages(context=context_text, user_message=state['user_message']),
            response_format={"type": "json_object"}
        )
        print("Received response from Groq.")
        content = response.content
        result = json.loads(content)
    except Exception:
        # Fallback manual parsing if needed
        result = {
            "category": "Other", 
            "urgency": "Medium", 
            "reply": "Error generating structured response."
        }
        
    return {"response": result}

# 4. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()

def process_inquiry_with_llm(user_message: str):
    """
    Entry point for the API
    """
    try:
        print(f"Processing inquiry: {user_message}")
        inputs = {"user_message": user_message}
        print("Invoking LangGraph workflow...")
        result = app.invoke(inputs)
        print("Workflow finished.")
        return result["response"]
    except Exception as e:
        print(f"Error in RAG pipeline: {e}")
        return {
            "category": "Other",
            "urgency": "Medium",
            "reply": f"Processing failed: {str(e)}"
        }
