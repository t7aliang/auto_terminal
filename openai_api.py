import os

def get_openai_api_key():
    # 从环境变量中获取 OpenAI API Key
    return os.getenv("OPENAI_API_KEY")
