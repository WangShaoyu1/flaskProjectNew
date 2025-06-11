import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np

# 1. 定义肯定和否定的关键词库（已扩充）
affirmative_keywords = [
    "是的", "行", "好", "好吧", "可以", "马上", "准备好了", "确认", "启动", "启动吧",
    "对的", "确实", "没问题", "当然", "完全可以", "没错", "就是这样", "我同意", "可以的", "答应",
    "我愿意", "没问题的", "是的，好的", "行，没问题", "好的，我同意", "好的，准备好了", "确实如此",
    "当然可以", "准备好了，开始吧", "是的，开始吧", "好吧，马上开始", "没问题，我来", "我准备好了"
]
negative_keywords = [
    "不", "不行", "不要", "不能", "不能够", "否", "暂时不", "不会", "不是",
    "绝对不", "不允许", "拒绝", "不能接受", "不愿意", "不可", "不想", "没戏", "不能做",
    "不答应", "不想做", "没有", "不喜欢", "不支持", "无法", "无法接受", "不可以", "不行的",
    "不会的", "我不同意", "不能做", "不行，不可能", "拒绝，我不答应", "我不愿意做", "不能答应",
    "不做", "不赞成", "不愿意", "绝不", "不希望", "不可以，我拒绝", "不是，我不行", "不行，我拒绝",
    "不可能", "不做这个决定", "不合适", "不接受"
]


# 2. 简单的正则表达式和规则判断
def simple_match(text):
    # 通过关键词库进行匹配
    for word in affirmative_keywords:
        if word in text:
            return "肯定"
    for word in negative_keywords:
        if word in text:
            return "否定"
    return "未确定"


# 3. 上下文规则判断（简单的否定规则）
def context_rule(text):
    # 例如，若包含"不想" 或 "不能" 之类的短语，则为否定
    if "不想" in text or "不能" in text or "不做" in text:
        return "否定"
    return "未确定"


# 4. 机器学习模型 - 使用TF-IDF 和 逻辑回归进行分类
class SimpleTextClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.model = LogisticRegression()

    def train(self, X_train, y_train):
        # 转换文本数据为TF-IDF特征
        X_train_vec = self.vectorizer.fit_transform(X_train)
        # 训练逻辑回归模型
        self.model.fit(X_train_vec, y_train)

    def predict(self, text):
        # 将输入文本转换为TF-IDF特征
        text_vec = self.vectorizer.transform([text])
        return self.model.predict(text_vec)[0]


# 5. 扩充训练数据
X_train = [
    "是的，好的", "行，没问题", "我可以", "马上去做",
    "不行", "不能", "不想", "我不要", "不会", "不做",
    # 扩充的肯定样本
    "是的，我可以做这件事", "行，没问题，我马上去做", "好的，我已经准备好",
    "可以的，马上就来", "确认了，我会处理这个任务", "启动吧，立即开始", "我同意，开始吧",
    "没问题，启动吧", "没有问题，我马上去做", "好的，开始吧", "确实如此，完全可以",
    "没错，我可以做", "当然，开始吧", "答应了，马上开始", "准备好了，马上进行",
    "我同意，开始吧", "可以的，立即开始", "没有问题，开始执行", "是的，立即开始",
    "对的，我会做的", "我会处理这个任务", "是的，我准备好做了",
    # 扩充的否定样本
    "不，我不行", "我不想做这个", "不可以，我不能", "不好意思，我不能接受", "我不会做这个",
    "我不做这件事", "不好，我不愿意", "不能，绝对不行", "我不想答应", "我不接受", "我不同意，不行",
    "我不能，抱歉", "拒绝，不能接受", "不是的，我不能做", "不是，我不能", "不行，不可能", "我不喜欢这个",
    "不，绝对不会", "不要，我不做", "不，不想做", "我不做这个决定", "不行，不答应", "不可以，我不允许",
    "不是，我拒绝", "不，不合适", "暂时不行，我不能", "不，我不喜欢", "不愿意，我不接受", "我不想要",
    "我不愿意这么做", "我不同意，不做", "不可能，我不做", "不，这不合适", "不能，我不允许", "拒绝，我不答应",
    "我不同意做", "不能接受，我拒绝", "不行，绝对不行", "不愿意，我不做"
]

y_train = [
    "肯定", "肯定", "肯定", "肯定", "否定", "否定", "否定", "否定", "否定", "否定",
    # 对应的肯定标签
    "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定",
    "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定", "肯定",
    # 对应的否定标签
    "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定",
    "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定",
    "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定", "否定"
]

# 训练模型
classifier = SimpleTextClassifier()
classifier.train(X_train, y_train)


# 6. 综合判断方法
def classify_input(text):
    # 先用关键词匹配和规则进行初步判断
    result = simple_match(text)
    if result != "未确定":
        return result

    # 如果匹配不明确，尝试规则判断
    result = context_rule(text)
    if result != "未确定":
        return result

    # 如果仍然不明确，使用机器学习模型进行判断
    return classifier.predict(text)


# 7. 从文件读取测试用例并进行分类
def test_case_from_file(input_file_path, output_file_path):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            # 打开输出文件用于写入分类结果
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                for line in input_file:
                    test_input = line.strip()  # 去掉每行前后的空白字符
                    if test_input:
                        # 分类判断
                        result = classify_input(test_input)
                        # 将结果写入输出文件
                        output_file.write(f"输入: {test_input} -> 结果: {result}\n")
                        print(f"输入: {test_input} -> 结果: {result}")
    except Exception as e:
        print(f"读取文件失败: {e}")


# 主程序
if __name__ == "__main__":
    input_file_path = f"./test_sentences.txt"  # 用户输入文件路径
    output_file_path = f"./test_sentences_result_1.txt"  # 用户输入输出文件路径
    test_case_from_file(input_file_path, output_file_path)  # 从文件读取并测试
