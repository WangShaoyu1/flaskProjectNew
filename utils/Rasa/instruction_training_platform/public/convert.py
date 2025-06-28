import pandas as pd
import json


def excel_to_json(input_file, output_file):
    # 读取Excel文件
    df = pd.read_excel(input_file, engine='openpyxl')

    # 准备存储结果的列表
    intents_list = []

    # 跟踪当前意图的变量
    current_intent = None

    # 遍历每一行数据
    for _, row in df.iterrows():
        # 检查是否是新意图（当前行有指令标识）
        if pd.notna(row["指令标识"]):
            # 如果有正在处理的意图，先保存它
            if current_intent is not None:
                intents_list.append(current_intent)

            # 创建新意图对象
            current_intent = {
                "intent_name": str(row["指令标识"]),
                "description": str(row["指令名称"]) if pd.notna(row["指令名称"]) else "",
                "utterances": [],
                "responses": []
            }

            # 添加响应话术
            if pd.notna(row["执行成功话术"]):
                current_intent["responses"].append({
                    "type": "success",
                    "text": str(row["执行成功话术"])
                })

            if pd.notna(row["执行失败话术"]):
                current_intent["responses"].append({
                    "type": "fail",
                    "text": str(row["执行失败话术"])
                })

        # 如果当前行有相似问，添加到当前意图
        if current_intent is not None and pd.notna(row["相似问"]):
            # 支持逗号分隔的多个问句
            similarities = str(row["相似问"]).split(",")
            for s in similarities:
                s_clean = s.strip()
                if s_clean:  # 忽略空字符串
                    current_intent["utterances"].append(s_clean)

    # 添加最后一个意图
    if current_intent is not None:
        intents_list.append(current_intent)

    # 构建完整的JSON结构
    result = {"intents": intents_list}

    # 写入JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    input_excel = "./403/command_403_1750175580.xlsx"  # 修改为您的Excel文件名
    output_json = "intents.json"  # 输出JSON文件名

    excel_to_json(input_excel, output_json)
    print(f"成功将Excel数据转换为JSON格式，输出文件: {output_json}")
