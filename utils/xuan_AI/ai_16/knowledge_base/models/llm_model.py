
from langchain.chat_models import ChatOpenAI
from langchain.llms import HuggingFaceHub
from config.keys import Keys
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings

# 核心关注点temperature=0
# 对于知识库我们要求内容要严谨，不可随意发挥
def get_openai_model():
    llm_model = ChatOpenAI(openai_api_key=Keys.OPENAI_API_KEY,
                           model_name=Keys.MODEL_NAME,
                           openai_api_base=Keys.OPENAI_API_BASE,
                           temperature=0)
    return llm_model


def get_openaiEmbedding_model():
    return OpenAIEmbeddings(openai_api_key=Keys.OPENAI_API_KEY,
                            openai_api_base=Keys.OPENAI_API_BASE)



"""
备选方案
"""
def get_huggingfacehub(model_name=None):
    llm_model = HuggingFaceHub(repo_id=model_name,
                               huggingfacehub_api_token=Keys.HUGGINGFACEHUB_API_TOKEN)
    return llm_model

def get_huggingfaceEmbedding_model(model_name):
    return HuggingFaceInstructEmbeddings(model_name=model_name)
