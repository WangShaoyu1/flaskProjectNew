import logging
import json
import structlog
import os


def setup_structlog(log_filename="app.log"):
    """
    设置structlog和logging的配置，并返回配置好的日志记录器。

    :param log_filename: 要写入日志的文件名
    :return: 配置好的structlog日志记录器
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_filename)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 自定义处理器来处理日志消息中的JSON部分
    def expand_json_in_event(logger, log_method, event_dict):
        event = event_dict.get("event", "")
        try:
            # 查找日志消息中的 JSON 部分
            if isinstance(event, str):
                start = event.find('{')
                end = event.rfind('}') + 1
                if start != -1 and end != -1:
                    json_part = event[start:end]
                    try:
                        # 尝试解析 JSON
                        parsed_json = json.loads(json_part)
                        if isinstance(parsed_json, (dict, list)):
                            # 格式化 JSON 内容
                            formatted_json = json.dumps(parsed_json, ensure_ascii=False, indent=4)
                            # 更新日志内容
                            event_dict.update({"event": event[:start].strip() + formatted_json + event[end:].strip()})
                    except json.JSONDecodeError:
                        # 如果解析失败，保持原样
                        pass
        except (json.JSONDecodeError, TypeError):
            # 忽略 JSON 解析错误
            pass

        print(f"event_dict: {event_dict}")
        return event_dict

    # 自定义 JSON 渲染器
    def custom_json_renderer(_, __, event_dict):
        """
        自定义 JSON 渲染器，确保输出可读的 JSON 格式，并保留中文字符
        """
        msg = event_dict.get('event', '')

        # 如果消息以 "---------" 开头，原样输出，不添加 event 和 level 信息
        if msg.startswith('---------'):
            return msg
        # 确保 msg 字段是字符串，如果 msg 是字典或列表则转换为 JSON 字符串
        if 'msg' in event_dict:
            if isinstance(event_dict['msg'], (dict, list)):
                event_dict['msg'] = json.dumps(event_dict['msg'], ensure_ascii=False, indent=4)
            elif isinstance(event_dict['msg'], str):
                try:
                    # 尝试解析 msg 字符串，如果是有效 JSON 则格式化
                    parsed_msg = json.loads(event_dict['msg'])
                    event_dict['msg'] = json.dumps(parsed_msg, ensure_ascii=False, indent=4)
                except json.JSONDecodeError:
                    # 如果不是有效 JSON，则保持原样
                    pass

        return json.dumps(event_dict, ensure_ascii=False, indent=4)

    # 设置 logging 配置
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()]
    )

    # 配置 structlog 处理器
    structlog.configure(
        processors=[
            expand_json_in_event,  # 自定义处理器，解析日志消息中的JSON部分
            # structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            # structlog.processors.JSONRenderer(indent=4),  # JSON格式化输出，带缩进
            custom_json_renderer
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 返回配置好的日志记录器
    return structlog.get_logger()


if __name__ == "__main__":
    logger = setup_structlog("logs/example1.log")

    logger.info("[{'role': 'user', 'content': '重新再来'}]")

    logger.info("这是英文: {\"action\": \"login\", \"user\": \"john_doe\", \"status\": \"success\"} completed.")
