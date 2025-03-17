import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()
OPEN_API_KEY = os.getenv('OPEN_API_KEY')

class LLMRequest():
    @staticmethod
    def sendRequest(devPrompt, request, AIModel='o3-mini'):
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model=AIModel,
            messages=[
                {"role": "developer", "content": f"{devPrompt}"},
                {"role": "user", "content": f"{request}"}
            ]
        )
        return completion