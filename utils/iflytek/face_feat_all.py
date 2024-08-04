# -*- coding: utf-8 -*-
import datetime
import os
from utils import util
import asyncio
import aiohttp
from face_feat_anys_age import fetch_age
from face_feat_anys_gender import fetch_gender
from face_feat_anys_score import fetch_face_score
from face_feat_anys_expression import fetch_expression

# 记录次数的文件路径
times_file = 'temp_data_dir/times.txt'
FilePath = fr"D:\gitlab\flaskProjectNew\app\static\img\test"
# 初始化 times 的值
if os.path.exists(times_file):
    with open(times_file, 'r') as f:
        times = int(f.read().strip())
else:
    times = 0


def write_txt_requests(a, b, c, d):
    util.write_to_file('temp_data_dir/iflytek.log',
                       f'----------{datetime.datetime.now().strftime("%m月%d日 %H时%M分%S秒")}------第{times}次----\n')

    util.write_to_file('temp_data_dir/iflytek.log', f'------------age年龄\n')
    util.write_to_file('temp_data_dir/iflytek.log', f"{a['data']}")
    util.write_to_file('temp_data_dir/iflytek.log', f"---耗时：{a['duration']}秒\n")

    util.write_to_file('temp_data_dir/iflytek.log', f'------------gender性别\n')
    util.write_to_file('temp_data_dir/iflytek.log', f"{b['data']}")
    util.write_to_file('temp_data_dir/iflytek.log', f"---耗时：{b['duration']}秒\n")

    util.write_to_file('temp_data_dir/iflytek.log', f'------------face_score颜值\n')
    util.write_to_file('temp_data_dir/iflytek.log', f"{c['data']}")
    util.write_to_file('temp_data_dir/iflytek.log', f"---耗时：{c['duration']}秒\n")

    util.write_to_file('temp_data_dir/iflytek.log', f'------------expression表情\n')
    util.write_to_file('temp_data_dir/iflytek.log', f"{d['data']}")
    util.write_to_file('temp_data_dir/iflytek.log', f"---耗时：{d['duration']}秒\n")

    print(f'--------------------all success----------------------\n')


def write_txt(all_data):
    def write_data_seperate():
        for data in all_data:
            util.write_to_file('temp_data_dir/iflytek.log', f"{data['age']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log', f"---年龄age耗时：{data['age']['duration']}秒\n")

            util.write_to_file('temp_data_dir/iflytek.log', f"{data['gender']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log', f"---性别gender耗时：{data['gender']['duration']}秒\n")

            util.write_to_file('temp_data_dir/iflytek.log', f"{data['face_score']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log',
                               f"---颜值face_score耗时：{data['face_score']['duration']}秒\n")

            util.write_to_file('temp_data_dir/iflytek.log', f"{data['expression']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log',
                               f"---表情expression耗时：{data['expression']['duration']}秒\n")

        print(f'--------------------all success----------------------\n')
        util.write_to_file('temp_data_dir/iflytek.log', f'--------------------all success----------------------\n')

    def write_data_center():
        for i in range(len(all_data)):
            util.write_to_file('temp_data_dir/iflytek.log', f"{all_data[i]['age']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log', f"---年龄age耗时：{all_data[i]['age']['duration']}秒\n")

        for i in range(len(all_data)):
            util.write_to_file('temp_data_dir/iflytek.log', f"{all_data[i]['gender']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log',
                               f"---性别gender耗时：{all_data[i]['gender']['duration']}秒\n")

        for i in range(len(all_data)):
            util.write_to_file('temp_data_dir/iflytek.log', f"{all_data[i]['face_score']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log',
                               f"---颜值face_score耗时：{all_data[i]['face_score']['duration']}秒\n")

        for i in range(len(all_data)):
            util.write_to_file('temp_data_dir/iflytek.log', f"{all_data[i]['expression']['data']}")
            util.write_to_file('temp_data_dir/iflytek.log',
                               f"---表情expression耗时：{all_data[i]['expression']['duration']}秒\n")

        print(f'--------------------all success----------------------\n')
        util.write_to_file('temp_data_dir/iflytek.log', f'--------------------all success----------------------\n')

    def write_data_more_images():
        image_count = get_image_count(FilePath)
        cycle_times = len(all_data) // image_count
        result = []
        for i in range(image_count):
            result.append([[] for _ in range(cycle_times)])
            for j in range(cycle_times):
                result[i][j] = all_data[i + image_count * j]

        for i in range(len(result)):
            util.write_to_file('temp_data_dir/iflytek.log',
                               f"\n\n--------------------{result[i][0]['image_name']}----------------------\n")
            for j in range(len(result[i])):
                util.write_to_file('temp_data_dir/iflytek.log', f"{result[i][j]['age']['data']}")
                util.write_to_file('temp_data_dir/iflytek.log', f"---年龄age耗时：{result[i][j]['age']['duration']}秒\n")
            util.write_to_file('temp_data_dir/iflytek.log', f"\n")

            for j in range(len(result[i])):
                util.write_to_file('temp_data_dir/iflytek.log', f"{result[i][j]['gender']['data']}")
                util.write_to_file('temp_data_dir/iflytek.log',
                                   f"---性别gender耗时：{result[i][j]['gender']['duration']}秒\n")
            util.write_to_file('temp_data_dir/iflytek.log', f"\n")

            for j in range(len(result[i])):
                util.write_to_file('temp_data_dir/iflytek.log', f"{result[i][j]['face_score']['data']}")
                util.write_to_file('temp_data_dir/iflytek.log',
                                   f"---颜值face_score耗时：{result[i][j]['face_score']['duration']}秒\n")
            util.write_to_file('temp_data_dir/iflytek.log', f"\n")

            for j in range(len(result[i])):
                util.write_to_file('temp_data_dir/iflytek.log', f"{result[i][j]['expression']['data']}")
                util.write_to_file('temp_data_dir/iflytek.log',
                                   f"---表情expression耗时：{result[i][j]['expression']['duration']}秒\n")

        print(f'--------------------all success----------------------\n')
        util.write_to_file('temp_data_dir/iflytek.log', f'--------------------all success----------------------\n')

    write_data_more_images()


def get_image_files(directory):
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tif')
    return [file for file in os.listdir(directory) if file.lower().endswith(image_extensions)]


def get_image_count(directory):
    image_files = get_image_files(directory)
    return len(image_files)


async def process_image(session, image_name, file_path):
    r_age, duration_age = await fetch_age(session, image_name, file_path)
    r_gender, duration_gender = await fetch_gender(session, image_name, file_path)
    r_face_score, duration_face_score = await fetch_face_score(session, image_name, file_path)
    r_expression, duration_expression = await fetch_expression(session, image_name, file_path)

    result = {
        "image_name": image_name,
        "age": {"data": r_age, "duration": duration_age},
        "gender": {"data": r_gender, "duration": duration_gender},
        "face_score": {"data": r_face_score, "duration": duration_face_score},
        "expression": {"data": r_expression, "duration": duration_expression},
    }

    return result


async def process_all_images():
    async with aiohttp.ClientSession() as session:
        image_files = get_image_files(FilePath)
        all_results = []
        for image_name in image_files:
            file_path = os.path.join(FilePath, image_name)
            result = await process_image(session, image_name, file_path)
            all_results.append(result)
            await asyncio.sleep(1)  # 为了避免请求过于频繁，可以加入适当的延时

    return all_results


async def main():
    global times
    all_data = []
    for i in range(10):
        times += 1
        result = await process_all_images()
        all_data.extend(result)  # 将每批图片处理的结果添加到总的结果列表中
        await asyncio.sleep(5)  # 增加5秒间隔

    print(f"all_data: {len(all_data)}")
    write_txt(all_data)

    # 保存 times 的值
    with open(times_file, 'w') as f:
        f.write(str(times))


if __name__ == "__main__":
    # 运行异步主程序
    asyncio.run(main())
