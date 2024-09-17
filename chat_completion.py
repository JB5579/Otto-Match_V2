import os
from openai import OpenAI
from langgraph import LangGraph
import markdown
import docx

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Initialize LangGraph
langgraph = LangGraph()

def load_knowledge_base(folder_path):
    knowledge_base = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith('.txt'):
            with open(file_path, 'r') as file:
                knowledge_base[filename] = file.read()
        elif filename.endswith('.md'):
            with open(file_path, 'r') as file:
                md_content = file.read()
                knowledge_base[filename] = markdown.markdown(md_content)
        elif filename.endswith('.docx'):
            doc = docx.Document(file_path)
            doc_content = "\n".join([para.text for para in doc.paragraphs])
            knowledge_base[filename] = doc_content
        # Add more file type handling here as needed
    return knowledge_base

def index_knowledge_base(knowledge_base):
    for doc_id, content in knowledge_base.items():
        langgraph.add_document(doc_id, content)

# Load and index the knowledge base at startup
KNOWLEDGE_BASE_FOLDER = 'Knowledge_File'
knowledge_base = load_knowledge_base(KNOWLEDGE_BASE_FOLDER)
index_knowledge_base(knowledge_base)

def retrieve_relevant_documents(query):
    # Retrieve documents based on the query
    documents = langgraph.retrieve(query)
    
    # Sort documents by relevance score (assuming langgraph.retrieve returns a list of tuples (doc_id, score))
    sorted_documents = sorted(documents, key=lambda x: x[1], reverse=True)
    
    # Extract the document IDs from the sorted list
    relevant_doc_ids = [doc_id for doc_id, score in sorted_documents]
    
    # Return the content of the relevant documents
    relevant_documents = [knowledge_base[doc_id] for doc_id in relevant_doc_ids if doc_id in knowledge_base]
    
    return relevant_documents

def send_openrouter_request(conversation_history):
    user_message = conversation_history[-1]['content']
    relevant_documents = retrieve_relevant_documents(user_message)

    try:
        completion = openrouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://jonathanbrockmanchatbot.com",
                "X-Title": "Jonathan Brockman Chatbot",
            },
            model="openai/gpt-4o-mini-2024-07-18",
            messages=conversation_history + [
                {
                    "role": "system",
                    "content": "\n".join(relevant_documents)
                }
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error in OpenRouter API call: {str(e)}")
