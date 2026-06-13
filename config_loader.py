import configparser
import os
import json
from typing import List, Tuple


def load_schedule(config_file=None):
    """从 schedule.json 或 schedule.ini 加载时间段配置，返回 list[(start_min, end_min, name)].
    如果读取失败或空，则返回默认值。
    """
    # 首先尝试加载JSON配置文件
    json_file = "schedule.json"
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                activities = data.get("activities", [])
                if activities:
                    # 转换为所需格式 [(start_min, end_min, name)]
                    schedule = [(act["start"], act["end"], act["name"]) for act in activities]
                    print(f"成功从 {json_file} 加载活动配置: {schedule}")  # 调试信息
                    return schedule
                else:
                    print(f"{json_file} 中没有活动配置")  # 调试信息
        except json.JSONDecodeError as e:
            print(f"JSON格式错误：{e}")
        except Exception as e:
            print(f"读取JSON课程时间表失败：{e}")

    # 如果没有JSON配置文件或读取失败，则尝试INI配置文件
    if config_file is None:
        config_file = os.path.join(os.getcwd(), "schedule.ini")

    print(f"尝试从INI文件加载配置: {config_file}")  # 调试信息
    config = configparser.ConfigParser()
    schedule = []
    try:
        config.read(config_file, encoding='utf-8')
        if 'Schedule' in config:
            for key, value in config['Schedule'].items():
                if key.startswith('period'):
                    cleaned_value = value.split('#')[0].strip()
                    start, end = map(int, cleaned_value.split('-'))
                    name_key = f"name_{key.split('_')[1]}"
                    period_name = config['Schedule'].get(name_key, f"时段 {key.split('_')[1]}")
                    schedule.append((start, end, period_name))
            print(f"从INI文件加载到配置: {schedule}")  # 调试信息
    except Exception as e:
        print(f"读取课程时间表失败：{e}，使用默认时间表")

    if not schedule:
        schedule = [(1140, 1230, "晚修1"), (1245, 1310, "晚修2")]
        print("使用默认时间表")  # 调试信息

    return schedule