import os
from openai import OpenAI
from langgraph import LangGraph

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
        with open(os.path.join(folder_path, filename), 'r') as file:
            knowledge_base[filename] = file.read()
    return knowledge_base

def index_knowledge_base(knowledge_base):
    for doc_id, content in knowledge_base.items():
        langgraph.add_document(doc_id, content)

def retrieve_relevant_documents(query):
    return langgraph.retrieve(query)

def send_openrouter_request(conversation_history):
    knowledge_base = load_knowledge_base('path_to_knowledge_base_folder')
    index_knowledge_base(knowledge_base)

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
