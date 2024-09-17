import os
from openai import OpenAI

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

knowledge_base = """
Jonathan Brockman is a passionate AI enthusiast with a focus on ethical implementation.
He is a creative problem-solver who thrives in collaborative environments and has an
entrepreneurial spirit coupled with a strong work ethic. Jonathan has diverse interests
and is a self-driven learner. He is principled and success-oriented but not at the expense
of personal values. Jonathan deeply cares about people and the societal impact of AI.
He is inquisitive, humble, and engaging in conversations.
"""

def send_openrouter_request(message: str) -> str:
    try:
        completion = openrouter_client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://jonathanbrockmanchatbot.com",
                "X-Title": "Jonathan Brockman Chatbot",
            },
            model="openai/gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "system",
                    "content": knowledge_base
                },
                {
                    "role": "user",
                    "content": message,
                },
                {
                    "role": "assistant",
                    "content": """
                    I am an AI assistant named JB, designed to represent Jonathan Brockman 
                    during initial interview conversations. When addressed with direct questions 
                    in the first person, I will respond as Jonathan Brockman would.
                    """
                },
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error in OpenRouter API call: {str(e)}")
