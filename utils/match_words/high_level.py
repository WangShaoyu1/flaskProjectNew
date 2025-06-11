import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
import joblib

# 下载必要的资源
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')

# 初始化情感分析工具
sia = SentimentIntensityAnalyzer()

# 定义肯定和否定的词汇和语法规则
affirmative_keywords = ["是的", "行的", "可以", "启动", "开始", "动手", "准备好了", "搞定", "马上", "好的", "确定"]
negative_keywords = ["不要", "不需要", "不行", "不", "先别", "暂时不", "停止", "取消", "拒绝", "不开始", "否认"]


# 情感分析函数，返回是否为肯定或否定
def sentiment_analysis(statement):
    sentiment_score = sia.polarity_scores(statement)
    return '肯定' if sentiment_score['compound'] >= 0.05 else '否定'


# 复杂的规则分类函数，基于否定/肯定关键词以及情感分析
def classify_statement(statement):
    statement = statement.strip().lower()

    # 如果语句包含肯定关键词，则直接分类为肯定
    if any(word in statement for word in affirmative_keywords):
        return "肯定"

    # 如果语句包含否定关键词，则直接分类为否定
    elif any(word in statement for word in negative_keywords):
        return "否定"

    # 情感分析辅助判断
    sentiment_result = sentiment_analysis(statement)
    if sentiment_result == "肯定":
        return "肯定"
    else:
        return "否定"


# 预处理文本：分词、去除停用词
def preprocess_text(text):
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))  # 如果是中文，可考虑使用对应的中文停用词
    tokens = [word for word in tokens if word.lower() not in stop_words]
    return ' '.join(tokens)


# 读取文件并进行批量处理
def process_statements(input_file):
    # 用于存储分类结果
    results = []

    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as file:
        statements = file.readlines()

    # 对每条语句进行分类
    for statement in statements:
        statement = statement.strip()
        result = classify_statement(statement)
        results.append((statement, result))

    return results


# 用机器学习方法进行训练并预测（如果有足够的数据）
def train_model():
    # 假设你已经有了训练数据，并且标注了“肯定”和“否定”的标签
    # 训练数据 (这里的数据集需要你自己提供或构造)
    train_data = ["我不想启动", "好的，开始吧", "取消操作", "可以启动", "不需要", "是的，开始"]
    labels = ["否定", "肯定", "否定", "肯定", "否定", "肯定"]

    # TF-IDF 向量化
    vectorizer = TfidfVectorizer()
    X_train = vectorizer.fit_transform(train_data)

    # 训练分类模型
    model = SVC(kernel='linear')
    model.fit(X_train, labels)

    # 保存模型
    joblib.dump(model, 'classifier_model.pkl')
    joblib.dump(vectorizer, 'vectorizer.pkl')


def predict_using_model(input_file):
    # 加载模型和向量化器
    model = joblib.load('classifier_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')

    # 读取待预测文本
    with open(input_file, 'r', encoding='utf-8') as file:
        statements = file.readlines()

    # 对每条语句进行预测
    results = []
    for statement in statements:
        statement = statement.strip()
        vectorized_input = vectorizer.transform([statement])
        prediction = model.predict(vectorized_input)
        results.append((statement, prediction[0]))

    return results


def main():
    # 选择使用哪种方式
    input_file = 'verified_results.txt'  # 输入文件路径

    # 如果需要训练模型，可以调用train_model()一次
    # train_model()

    # 使用模型进行预测（如果你有训练数据）
    # results = predict_using_model(input_file)

    # 使用基于规则的分类进行处理
    results = process_statements(input_file)

    # 输出每条语句的分类结果
    for statement, result in results:
        print(f"语句: {statement} -> 分类: {result}")


if __name__ == "__main__":
    main()
