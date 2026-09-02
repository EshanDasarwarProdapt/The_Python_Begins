import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    timeout=60.0,
    max_retries=1
)
try:
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_CHAT_MODEL"),
        messages=[{"role": "user", "content": "Hello"}],
    )
    print("Success:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
