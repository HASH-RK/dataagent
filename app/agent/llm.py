import os

from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

# llm = init_chat_model(
#     model="qwen-plus",
#     model_provider="openai",
#     base_url=os.getenv("DASHSCOPE_BASE_URL"),
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     temperature=0, # 不要创意
# )

llm = init_chat_model(
    model=app_config.llm.model_name,
    api_key=app_config.llm.api_key,
    temperature=0, # 不要创意
)

if __name__ == '__main__':
    result = llm.invoke("你是什么模型？")
    print(result.content)