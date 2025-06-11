import re
import time

# 1. 定义肯定和否定的关键词库
affirmative_keywords = [
    "是的", "行", "好的", "好", "可以", "确认", "对", "没问题", "没错", "当然", "需要", "要", "要的",
    "没事", "好吧", "没关系", "对的", "是", "我同意", "行的", "好呀", "没问题的", "当然可以",
    "可以的", "必定", "同意", "认同", "完全同意", "是这样", "绝对", "完全是", "很棒", "有的",
    "可以吧", "非常好", "一切OK", "确实", "非常愿意", "马上", "立刻", "行得通", "我愿意", "没错呀",
    "确定", "好的吧", "完全同意", "一切顺利", "非常棒", "一切都好", "我答应", "我同意的", "肯定的",
    "可以做到", "没问题啦", "答应", "已经准备好", "十分肯定", "确实如此", "当然愿意", "毫无问题",
    "好得没话说", "一切安排妥当", "没有问题", "没异议", "同意的", "没疑问", "没有疑虑", "没有反对",
    "绝对没问题", "我全力支持", "是的，我同意", "愿意", "做的好", "好极了", "你说的对", "毫不犹豫",
    "绝对支持", "对呀", "好像是", "当然行", "一切OK", "当然可以", "完美", "太棒了", "完全行",
    "同样同意", "就这么办", "走吧", "可以去做", "完全同意", "就这样决定", "放心，行", "正好",
    "我很高兴", "做吧", "确认无误", "我愿意做", "非常好", "顺利完成", "是这样", "确凿无疑", "是的，确认",
    "没问题啦", "我全力支持", "ok", "yes", "I agree", "sure", "alright", "fine", "perfect", "correct",
    "开始", "启动", "搞起来", "运行"
]

negative_keywords = [
    "不", "不能", "不是", "没", "没有", "不行", "不做", "不要", "不能够", "不想", "不答应", "取消", "算逑", "等等",
    "等会", "不可能", "绝对不", "不是的", "不支持", "拒绝", "不允许", "不可", "无意", "算了", "不同意", "不接受", "别",
    "不接受", "不想做", "不愿意", "不赞同", "不希望", "不会的", "不再", "不管", "不承认", "不需要", "不赞成", "不想要",
    "拒绝接受", "没准备好", "no", "not", "never", "no way", "I don't think so",
    "I disagree", "not at all", "nope", "can't", "don't want", "not possible", "no thanks"
]

# 避免出现 需要 和 不需要，意思完全相反但是优先匹配到 需要，从而导致语义错误
negative_patterns = [
    r"(不|不做|不允许|不再|不去|不可以|不希望|不想|不想做|不想要|不愿|不愿意|不接受|不是|不用|不能|不能够|不行|不要|不许|不需要|停|别|别做|拒绝|无|没有|没有|不再|没法|等会).*?("
    r"启动|继续|开始|运行|执行|进行|做|去|要|想)"]

# 定义常见的语气词和副词
filler_words = ["了", "阿", "呀", "吧", "的", "嘛", "啊", "呢", "就", "可", "总之", "即使", "非常", "有点", "其实",
                "稍微", "不太", "怎么", "因此", "就", "才", "更", "也"]

# 常见的问句词汇
question_words = [
    "什么是", "什么是", "如何", "为什么", "怎么", "哪里", "谁是", "能否", "是否", "有没有", "怎样", "什么样",
    "哪儿", "多大", "什么时候", "怎么样", "能不能", "几时", "哪些", "几何", "要不要", "多少", "多么",
    "为啥", "如何是", "会不会", "是不是", "该怎么", "能够", "应该", "有没有办法", "哪种", "如何做",
    "是不是", "为什么会", "这是什么", "这些", "如何理解", "怎么做", "为什么会这样", "做什么", "该如何",
    "如何改善", "如何解决", "哪里可以", "怎样才能", "有多远", "有多少", "怎样才", "怎么用", "怎么解决", "吗", "么", "呢"
]

# 对肯定词和否定词按照词汇长度排序（从长到短）
affirmative_keywords = sorted(affirmative_keywords, key=lambda x: len(x), reverse=True)
negative_keywords = sorted(negative_keywords, key=lambda x: len(x), reverse=True)


# 2. 简单的正则表达式和规则判断
def simple_match(text):
    # 去掉文本中的空格、标点符号和字母转换为小写
    cleaned_text = re.sub(r'[^\w\s]', '', text).lower()  # 去掉标点符号、转换为小写
    cleaned_text = " ".join([word for word in cleaned_text.split() if word not in filler_words])  # 去除语气词和副词

    # 如果是疑问句
    if any(question_word in cleaned_text for question_word in question_words):
        return "未确定"

    # 保存匹配到的肯定词和否定词
    affirmative_matches = []
    negative_matches = []

    # 使用否定表达式匹配
    for pattern in negative_patterns:
        match = re.search(pattern, cleaned_text)
        if match:
            negative_matches.append((match.group(), match.start()))
            cleaned_text = re.sub(pattern, len(match.group()) * "*", cleaned_text)
            print(f"匹配到否定表达式: {match.group()}----{text}----{cleaned_text}")

    # 匹配否定词
    for word in negative_keywords:
        if word in cleaned_text:
            negative_matches.append((word, cleaned_text.index(word)))
            cleaned_text = cleaned_text.replace(word, len(word) * "*")
            print(f"匹配到否定词: {word} ---- {text}----{cleaned_text}")

    # 否定没有匹配，再检查肯定词
    for word in affirmative_keywords:
        if word in cleaned_text:
            affirmative_matches.append((word, cleaned_text.index(word)))
            cleaned_text = cleaned_text.replace(word, len(word) * "*")
            print(f"匹配到肯定词: {word}----{text}----{cleaned_text}")

    # 优先判定否定词
    if negative_matches and affirmative_matches:
        # 获取肯定和否定词在句子中的位置，最大位置如果肯定在后，则整个句子表达为肯定；反之亦然
        affirmative_position = max(affirmative_matches, key=lambda x: x[1])[1]
        affirmative_max_match = max(affirmative_matches, key=lambda x: x[1])[0]
        negative_position = max(negative_matches, key=lambda x: x[1])[1]
        negative_max_match = max(negative_matches, key=lambda x: x[1])[0]
        print(f"affi: {affirmative_position}-{affirmative_max_match}, nega: {negative_position}-{negative_max_match}")
        # if len(affirmative_matches) > 1 or len(negative_matches) > 1:
        #     return "未确定"

        # 判断位置关系
        if affirmative_position <= negative_position:
            return "否定"  # 肯定在前，否定在后，返回否定
        elif negative_position + len(negative_max_match) == affirmative_position:
            return "否定"  # 否定在前，肯定在后，返回肯定
        else:
            return "未确定"

    elif negative_matches:
        return "否定"
    elif affirmative_matches:
        if len(affirmative_matches) == 1 and len(affirmative_matches[0][0]) == 1 and len(cleaned_text) >= 5:
            return "未确定"
        return "肯定"
    else:
        return "未确定"


# 5. 综合判断方法
def classify_input(text):
    # 先用关键词匹配和规则进行初步判断
    result = simple_match(text)
    if result != "未确定":
        return result

    # 如果仍然不明确，返回"未确定"
    return "未确定"


# 6. 从文件读取测试用例并进行分类
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
    start_time = time.time()
    # input_file_path = f"./tmp.txt"  # 用户输入文件路径
    input_file_path = f"./test_sentences.txt"  # 用户输入文件路径
    print(f"读取input_file耗时: {time.time() - start_time:.4f} 秒")
    output_file_path = f"./test_results_py.txt"  # 用户输入输出文件路径
    test_case_from_file(input_file_path, output_file_path)  # 从文件读取并测试
    print(f"总耗时: {time.time() - start_time:.4f} 秒")
