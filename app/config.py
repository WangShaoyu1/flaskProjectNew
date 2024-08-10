import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_BASE_URL = os.getenv('OPENAI_API_BASE_URL')
    GPT_MODEL_NAME = os.getenv('GPT_MODEL_NAME')
    ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
    ZHIPU_MODEL_NAME = os.getenv('ZHIPU_MODEL_NAME')
