import random
import re
from difflib import SequenceMatcher
from typing import List, Tuple


def microwave_test_pipeline() -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    生成测试句子并分类，返回测试句子及其分类结果。
    :return: (测试句子列表, 分类结果列表)
    """

    def is_similar(word1: str, word2: str, threshold: float = 0.8) -> bool:
        """判断两个词的相似度是否达到阈值"""
        return SequenceMatcher(None, word1.lower(), word2.lower()).ratio() >= threshold

    def tokenize(sentence: str) -> List[str]:
        """简单分词，按标点和空格分割"""
        return re.split(r'[\s,;.!?\u3000\uff0c\uff1b\u3002]+', sentence)

    def match_positive(input_text: str) -> bool:
        """匹配是否是肯定表达"""
        positive_words = [
            "要", "需要", "是", "好的", "好吧", "行", "成", "确定", "确认", "可以", "当然", "OK",
            "YES", "启动", "开始", "启动烹饪", "开始烹饪", "继续", "妥", "安排", "直接开始", "马上",
            "运行", "启动吧", "开始吧", "安排上", "搞定", "可以了", "启动程序", "启动功能", "开始执行",
            "继续执行", "来直接开始", "开启", "运行起来", "现在开始", "就绪", "马上开始", "动手",
            "搞起来", "确认启动", "准备好了", "进入运行", "OK可以", "直接运行", "马上动手", "干起来",
            "就这么定", "直接上", "操作开始", "进行启动", "搞事情", "准备启动", "任务开始", "运行吧"
        ]

        tokens = tokenize(input_text)

        # 完全匹配和大小写无关匹配
        for token in tokens:
            if token.isalpha() and token.lower() in map(str.lower, positive_words):
                return True
            elif token in positive_words:
                return True

        # 模糊匹配
        for token in tokens:
            for word in positive_words:
                if is_similar(token, word):
                    return True

        return False

    def classify_response(input_text: str) -> str:
        """根据输入文本分类为肯定或否定"""
        return "肯定" if match_positive(input_text) else "否定"

    def generate_test_sentences() -> List[str]:
        """生成300条测试句子，包括肯定和否定表达"""
        positive_phrases = [
            "好的，开始吧", "启动烹饪", "是的，马上开始", "确认开始", "当然启动", "可以，现在就运行",
            "搞起来，启动吧", "OK，启动烹饪", "来吧，启动", "准备好了，开始吧", "直接运行吧", "启动吧",
            "妥了，启动烹饪", "启动程序", "现在开始吧", "准备开始", "运行烹饪程序", "马上动手", "启动功能",
            "就这样，启动吧", "就绪，启动烹饪", "马上开始", "确认启动", "继续吧，运行烹饪", "执行吧",
            "可以的，启动吧", "没问题，搞定它", "开始运行", "任务启动", "是的，动手吧", "准备好了，运行吧",
            "启动操作", "进入运行", "动起来，启动", "来直接运行", "马上准备，开始", "可以启动", "直接开始运行",
            "烹饪开始吧", "行的，启动", "我准备好了", "现在启动烹饪", "任务开始", "搞事情吧，启动", "运行起来吧",
            "好，运行烹饪", "来吧，操作", "行了，开始", "动起来", "执行操作吧", "运行烹饪功能",
            "马上搞定", "启动吧，搞起来", "开始操作", "准备烹饪", "OK，启动吧", "确认烹饪", "直接上吧"
        ]

        negative_phrases = [
            "不了，不用了", "我还没准备好", "先等等吧", "不用启动", "暂时先别开始", "不需要烹饪", "取消吧",
            "我不想启动", "这个就先算了", "不开始", "等会再启动", "暂时不要", "不用搞", "否定，不启动",
            "取消操作", "我改变主意了，不烹饪了", "不要启动", "这个操作暂时不要", "我再想想", "算了吧，不用了",
            "不烹饪了", "放弃操作", "停止启动", "我暂时不需要", "先别启动", "不用了，谢谢", "否认，取消启动",
            "我不要启动", "再等一会儿", "暂停操作", "算了，先别动", "暂时先不启动", "不准备启动", "没准备好",
            "不进行操作", "先停一下", "不行，别启动", "不行，我取消", "不要运行", "我拒绝烹饪", "先取消吧",
            "不用开始了"
        ]

        all_phrases = positive_phrases + negative_phrases

        def add_length_variation(phrase):
            contexts = [
                "我觉得可以这样：", "确认一下，我说的是：", "实际上是这样的：", "现在我们可以这样处理：", "听我的：",
                "对了，还有：", "可以确认，现在开始：", "简单来说：", "如果你问我的话：", "具体情况是这样的："
            ]
            if random.random() < 0.5:  # 随机增加上下文
                return random.choice(contexts) + phrase
            return phrase

        return [add_length_variation(random.choice(all_phrases)) for _ in range(300)]

    # 生成测试句子
    test_sentences = generate_test_sentences()

    # 分类每一句测试句子
    results = [(sentence, classify_response(sentence)) for sentence in test_sentences]

    # 保存到文件
    with open("microwave_test_sentences_combined.txt", "w", encoding="utf-8") as file:
        file.write("\n".join([f"{sentence} => {result}" for sentence, result in results]))

    return test_sentences, results


# 调用函数
if __name__ == "__main__":
    test_sentences, results = microwave_test_pipeline()

    # 示例输出部分结果
    for sentence, result in results[:10]:
        print(f"输入: {sentence} => 分类: {result}")
