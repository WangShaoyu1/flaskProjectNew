import os
import json
import io
import time
import inspect
import pandas as pd
from app.config import Config
from zhipuai import ZhipuAI
from utils.util import extract_code_block

client = ZhipuAI(api_key=Config.ZHIPU_API_KEY)


def suwukong_function(data):
    """
    孙悟空算法函数，该函数定义了数据集计算过程
    :param data:必要参数，表示带入计算的数据表，用字符串进行表示
    :return:sunwukong_function函数计算后的结果，返回结果表示为JSON格式的Dataframe类型对象
    """
    data = io.StringIO(data)
    # 定义函数内部变量
    df_new = pd.read_csv(data, sep='\s+', index_col=0)
    res = df_new * 10
    return json.dumps(res.to_string())


def auto_function(functions_list):
    """
    Chat模型的function参数编写函数
    :param functions_list: 包含一个或者多个函数对象的列表
    :return: 满足Chatm模型function参数要求的函数functions对象
    """
    start_time = time.time()

    def functions_generate():
        # 创建空列表，用于保存每个函数的描述字典
        functions = []
        # 遍历函数列表
        for function in functions_list:
            # 获取函数的名称，用于保存到字典中
            function_name = function.__name__
            # 获取函数的源代码，用于保存到字典中
            function_description = inspect.getdoc(function)

            system_prompt = '以下是某函数的函数说明：%s，输出结果必须是一个JSON格式的字典，只输出这个字典即可，不要其他内容' % function_description
            # system_prompt = '以下是某函数的函数说明：%s,输出结果必须是一个JSON格式的字典，只输出这个字典即可，前后不需要任何前后修饰或说明的语句' % function_description
            user_prompt = '根据这个函数的函数说明，请帮我创建一个JSON格式的字典，这个字典有如下5点要求：\
                           1.字典总共有三个键值对；\
                           2.第一个键值对的Key是字符串name，value是该函数的名字：%s，也是字符串；\
                           3.第二个键值对的Key是字符串description，value是该函数的函数的功能说明，也是字符串；\
                           4.第三个键值对的Key是字符串parameters，value是一个JSON Schema对象，用于说明该函数的参数输入规范。\
                           5.输出结果必须是一个JSON格式的字典，只输出这个字典即可，前后不需要任何前后修饰或说明的语句' % function_name

            response = client.chat.completions.create(
                model=Config.ZHIPU_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            end_time = time.time()
            print(f"花费的时间为：{end_time - start_time}")
            json_str = extract_code_block(response.choices[0].message.content)
            json_function_description = json.loads(json_str)
            json_str = {"type": "function", "function": json_function_description}
            functions.append(json_str)

        return functions

    # 最大可以尝试4次
    max_attempts = 4
    attempts = 0
    funcs = []
    while attempts < max_attempts:
        try:
            funcs = functions_generate()
            break
        except Exception as e:
            attempts += 1
            print(f"第{attempts}次尝试，异常为：{e}")
            if attempts == max_attempts:
                print("已达到最大尝试次数，程序终止。")
                raise  # 重新引发最后一个异常
            else:
                print("正在重新运行...")
    return funcs


auto_function([suwukong_function])
