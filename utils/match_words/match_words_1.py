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

    def remove_context(sentence: str) -> str:
        """移除上下文短语，简化语句"""
        context_phrases = [
            "我觉得可以这样：", "确认一下，我说的是：", "实际上是这样的：", "现在我们可以这样处理：", "听我的：",
            "对了，还有：", "可以确认，现在开始：", "简单来说：", "如果你问我的话：", "具体情况是这样的："
        ]
        for phrase in context_phrases:
            sentence = sentence.replace(phrase, "")
        return sentence.strip()

    def match_positive(input_text: str) -> bool:
        """匹配是否是肯定表达"""
        positive_words = [
            "要", "需要", "是", "好的", "好吧", "行", "成", "确定", "确认", "可以", "当然", "OK",
            "YES", "启动", "开始", "继续", "妥", "安排", "直接开始", "马上", "运行", "启动吧",
            "开始吧", "搞定", "可以了", "任务启动", "动起来", "准备好了", "现在开始", "搞事情吧",
            "好嘞", "妥了，这样吧", "搞起来", "直接搞定", "直接运行"
        ]

        tokens = tokenize(input_text)

        # 优先完全匹配
        for token in tokens:
            if token.lower() in map(str.lower, positive_words):
                return True

        # 模糊匹配
        for token in tokens:
            for word in positive_words:
                if is_similar(token, word):
                    return True

        return False

    def match_negative(input_text: str) -> bool:
        """匹配是否是否定表达"""
        negative_words = [
            "不要", "不需要", "不行", "先别", "不", "暂时不", "不开始", "拒绝", "停止", "取消",
            "否认", "放弃", "不做", "没准备", "先停", "不可以", "我不想", "无法", "别运行", "算了",
            "这个算了吧", "暂时先别", "不运行", "不启动", "没搞定", "停了吧", "放弃任务", "取消操作"
        ]

        tokens = tokenize(input_text)

        # 优先完全匹配
        for token in tokens:
            if token.lower() in map(str.lower, negative_words):
                return True

        # 模糊匹配
        for token in tokens:
            for word in negative_words:
                if is_similar(token, word):
                    return True

        return False

    def classify_response(input_text: str) -> str:
        """根据输入文本分类为肯定或否定"""
        # 去除上下文，简化语句
        cleaned_text = remove_context(input_text)

        # 优先匹配肯定和否定
        if match_positive(cleaned_text):
            return "肯定"
        elif match_negative(cleaned_text):
            return "否定"
        return "否定"  # 默认分类为否定

    def generate_test_sentences() -> List[str]:
        """生成300条测试句子，包括肯定和否定表达"""
        positive_phrases = [
            "好的，开始吧", "启动烹饪", "是的，马上开始", "确认开始", "当然启动", "可以，现在就运行",
            "搞起来，启动吧", "OK，启动烹饪", "准备好了，开始吧", "直接运行吧", "启动吧"
        ]

        negative_phrases = [
            "不了，不用了", "我还没准备好", "先等等吧", "不用启动", "暂时先别开始", "不需要烹饪",
            "取消吧", "我不想启动", "这个就先算了", "不开始", "等会再启动", "暂时不要"
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
    with open("optimized_test_results.txt", "w", encoding="utf-8") as file:
        file.write("\n".join([f"{sentence} => {result}" for sentence, result in results]))

    return test_sentences, results


# 调用函数
if __name__ == "__main__":
    test_sentences, results = microwave_test_pipeline()

    # 示例输出部分结果
    for sentence, result in results[:10]:
        print(f"输入: {sentence} => 分类: {result}")
