import fasttext
import re

# 1. 定义肯定和否定的关键词库
affirmative_keywords = [
    "是的", "行", "好", "好吧", "可以", "马上", "准备好了", "确认", "启动", "启动吧",
    "OK", "Yes", "Sure", "Alright", "Absolutely", "Definitely", "Of course", "No problem", "Okay", "Got it",  # 英文肯定词
    "对", "同意", "赞成", "没问题", "肯定", "接受", "同样", "允许", "愿意", "确认", "答应", "行吧", "会", "完全同意",
    "当然", "可以的", "可以行", "可以做", "好呀", "可以啊", "我答应", "赞同", "正确", "没问题", "同样的", "放心",
    "对呀",
    "完全可以", "好啊", "没疑问", "就是", "正是", "好极了", "去做吧", "做吧", "相信", "是的没错", "好像", "对的"
]

negative_keywords = [
    "不", "不能", "不要", "不行", "没有", "不可以", "不想", "不做", "不会", "不是",  # 10条中文否定词汇
    "没用", "不对", "不愿意", "不可能", "无法", "不需要", "拒绝", "不喜欢", "不接受", "不希望",  # 10条中文否定词汇
    "不行的", "不舒服", "不合适", "不准", "不让", "不打算", "不这样", "不靠谱", "不真实", "不明白",  # 10条中文否定词汇
    "No", "Not", "Never", "Can't", "Don't"  # 5条英文否定词汇
]


# 2. 文本匹配进行初步判断
def simple_match(text):
    for word in affirmative_keywords:
        if word in text:
            return "肯定"
    for word in negative_keywords:
        if word in text:
            return "否定"
    return "未确定"


# 3. 加载预训练的 FastText 中文模型
# 假设已经下载并加载了 fasttext 模型（可以替换为你实际的模型路径）
model = fasttext.load_model('cc.zh.300.bin')  # 请根据实际模型路径调整


# 4. 使用 FastText 模型进行语义匹配，判断“不确定”状态
def predict_state(text):
    # 获取文本的向量表示
    text_vector = model.get_sentence_vector(text)
    # 简单的相似度计算，假设0.5为“未确定”的阈值
    similarity_threshold = 0.5

    # 这里通过一些其他算法或业务规则可以进一步调整，不确定的状态
    # 假设我们能通过向量空间距离与预定义的阈值来判断是否“不确定”
    if abs(text_vector[0]) < similarity_threshold:  # 这里只是示范，具体的相似度计算需要基于具体需求
        return "未确定"
    else:
        return "待判定"  # 示例：实际可以根据业务规则进一步处理


# 5. 综合判断方法
def classify_input(text):
    # 先通过关键词匹配进行初步判断
    result = simple_match(text)
    if result != "未确定":
        return result

    # 如果通过关键词没有判断出，再进行语义判断
    return predict_state(text)


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
    input_file_path = input("请输入测试用例文件路径: ")  # 用户输入文件路径
    output_file_path = input("请输入输出文件路径: ")  # 用户输入输出文件路径
    test_case_from_file(input_file_path, output_file_path)  # 从文件读取并测试
