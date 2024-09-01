from langchain.chat_models import ChatOpenAI
from langsmith.schemas import Dataset
from ragas import evaluate
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import retrieval_qa
import os
import openai
import time
from ragas.metrics import (
    answer_relevancy,
    faithfulness,
    context_recall,
    context_precision,
)

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.base_url = os.getenv("OPENAI_API_BASE_URL")
# os.environ['LANGCHAIN_TRACING_V2'] = "true"
# os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
# os.environ['LANGCHAIN_API_KEY'] = 'ls__e77bbf50f90949e082e66305f4b8972d'
# os.environ['LANGCHAIN_PROJECT'] = 'langchain-openai-langsmith01'


## pip install ragas

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

embedding_model = OpenAIEmbeddings()

doc_list = """
1. 什么是LangChain?
LangChain是一个开源框架,允许从事人工智能的开发者将例如GPT-4的大语言模型与外部计算和数据来源结合起来。该框架目前以Python或JavaScript包的形式提供。
2. 什么是大模型？
大模型（Large Language Models）是一种人工智能模型，被训练成理解和生成人类语言。
大模型通常是指具有数百万到数十亿参数的神经网络模型，需要大量的计算资源和存储空间来训练和存储，并且往往需要进行分布式计算和特殊的硬件加速技术。
3. 什么是AI？
ai是Artificial Intelligence的缩写，指的是人工智能；人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学；人工智能研究的一个主要目标是使机器能够胜任一些通常需要人类智能才能完成的复杂工作。
4. 我们的课程名字叫什么？
   《AI大模型工程师》
5. 俄罗斯的总统是谁？
   普京
"""

text_spliter = CharacterTextSplitter(separator="\n",
                                     chunk_size=500,
                                     chunk_overlap=80,
                                     length_function=len)
chunks = text_spliter.split_text(doc_list)

vectorstore = FAISS.from_texts(texts=chunks,
                               embedding=embedding_model)

qa_chain = retrieval_qa.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
)

## 20个
eval_questions = [
    "我们的课程名字叫什么？"
]

eval_answers = [
    "《AI大模型工程师》"
]

examples = [
    {"query": q, "ground_truths": [eval_answers[i]]}
    for i, q in enumerate(eval_questions)
]

## 看一下从知识库里搜索出来的答案
result = qa_chain({"query": eval_questions[0]})
print(result)
time.sleep(30)

# create evaluation chains
faithfulness_chain = RagasEvaluatorChain(metric=faithfulness)
answer_rel_chain = RagasEvaluatorChain(metric=answer_relevancy)
context_rel_chain = RagasEvaluatorChain(metric=context_precision)
context_recall_chain = RagasEvaluatorChain(metric=context_recall)

##预测值
predict = qa_chain.batch(examples)
##预测值与真实值对比
result1 = faithfulness_chain.evaluate(examples, predict)
print(result1)
time.sleep(30)

result2 = answer_rel_chain.evaluate(examples, predict)
print(result2)
time.sleep(30)

result3 = context_rel_chain.evaluate(examples, predict)
print(result3)
time.sleep(30)

result4 = context_recall_chain.evaluate(examples, predict)
print(result4)
