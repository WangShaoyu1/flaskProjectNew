import os
import json
import pandas as pd
import requests
from typing import Union, List, Optional, Dict
from dotenv import load_dotenv
from datetime import datetime

# 加载.env文件中的环境变量
load_dotenv()


class JsonProcessor:
    @staticmethod
    def merge_json_content(folder_path: str, merged_file: str = 'merged.json') -> Dict:
        """合并文件夹内所有JSON文件的content字段"""
        merged_content = []

        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'content' in data and isinstance(data['content'], list):
                            merged_content.extend(data['content'])
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"警告：文件 {filename} 读取失败（{str(e)}），跳过")

        merged_data = {"content": merged_content}
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)

        print(f"合并完成，结果已保存到: {merged_file}")
        return merged_data

    @staticmethod
    def fetch_api_data(
            base_url: str,
            params: Dict,
            exclude_keys: Optional[List[str]] = None,
            output_file: str = 'api_output.xlsx',
            archive_json: bool = True  # 新增参数，控制是否存档JSON
    ) -> bool:
        """
        从API获取数据并处理
        :param base_url: API基础URL
        :param params: 请求参数
        :param exclude_keys: 要排除的字段列表
        :param output_file: 输出Excel文件名
        :param archive_json: 是否将获取的数据存档为JSON文件
        """
        # 从.env读取Authorization
        token = os.getenv("YZ_LOG_SYSTEM_API_AUTH_TOKEN")
        if not token:
            print("错误：未在.env文件中找到YZ_LOG_SYSTEM_API_AUTH_TOKEN")
            return False

        headers = {
            "Authorization": f"{token}",  # 使用.env中的token
            # "Content-Type": "application/json"
        }

        # 获取总数量
        total = JsonProcessor._get_total_elements(base_url, params, headers)
        print(f"总数量: {total}")
        if total <= 0:
            print("错误：无法获取总数量")
            return False

        # 获取完整数据
        all_data = JsonProcessor._fetch_all_data(base_url, params, headers, total)
        if not all_data:
            print("错误：无法获取完整数据")
            return False

        # 新增：存档JSON数据
        if archive_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H")
            archive_filename = f"api_data_{timestamp}.json"
            try:
                with open(archive_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=4)
                print(f"API数据已存档到: {archive_filename}")
            except Exception as e:
                print(f"警告：JSON存档失败（{str(e)}），继续处理Excel导出")

        # 处理并输出Excel
        return JsonProcessor.json_to_excel(all_data, output_file, exclude_keys)

    @staticmethod
    def _get_total_elements(base_url: str, params: Dict, headers: Dict) -> int:
        """获取API数据总数"""
        try:
            temp_params = params.copy()
            temp_params['size'] = 1
            response = requests.get(base_url, params=temp_params, headers=headers)

            response.raise_for_status()
            return response.json().get('totalElements', -1)
        except Exception as e:
            print(f"获取总数量失败: {str(e)}")
            return -1

    @staticmethod
    def _fetch_all_data(base_url: str, params: Dict, headers: Dict, total: int) -> Optional[Dict]:
        """获取全部API数据"""
        try:
            params['size'] = total
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取完整数据失败: {str(e)}")
            return None

    @staticmethod
    def json_to_excel(
            json_data: Union[str, Dict],
            output_file: str = 'output.xlsx',
            exclude_keys: Optional[List[str]] = None
    ) -> bool:
        """将JSON数据写入Excel"""
        exclude_keys = exclude_keys or []

        try:
            data = json_data if isinstance(json_data, dict) else json.load(open(json_data, 'r', encoding='utf-8'))
            content = data.get('content', [])

            if not content:
                print("警告：content字段为空")
                return False

            df = pd.DataFrame(content)
            df = df.drop(columns=exclude_keys, errors='ignore')
            df.to_excel(output_file, index=False, engine='openpyxl')

            print(f"Excel文件已生成: {output_file}")
            if exclude_keys:
                print(f"排除的字段: {exclude_keys}")
            return True

        except Exception as e:
            print(f"错误: {str(e)}")
            return False


# 使用示例
if __name__ == "__main__":
    # 示例API参数
    api_params = {
        "page": 0,
        "sort": "create_time,desc",
        "cluster_name": "yingzi-prod",
        "create_time": ["2025-05-09 00:00:00", "2025-05-09 23:59:59"],
        "topic": "normal-yingzi-appservice-bfv"
    }

    # 从API获取数据（自动读取.env中的token）
    JsonProcessor.fetch_api_data(
        base_url="https://datacenter-api.yingzi.com/api/clog/normal/",
        params=api_params,
        exclude_keys=[
            "topic", "trace_id", "ptrace_id", "pspan_id",
            "br_trace_id", "k8s_pod_name", "thread_name",
            "class_name", "k8s_container_name", "error_type", "error_detail", "project_id"
        ],
        output_file=f"api_output_{datetime.now().strftime('%Y%m%d_%H')}.xlsx",
        archive_json=True  # 启用JSON存档
    )

    # 方式2：处理本地JSON文件（可选）
    # folder_path = 'json_files'
    # merged_data = JsonProcessor.merge_json_content(folder_path)
    # JsonProcessor.json_to_excel(merged_data, 'local_output.xlsx', exclude_keys)
