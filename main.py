import argparse
import yaml
from src.feishu import FeiShu
import urllib3
import urllib.parse
import requests
import logging

from datetime import datetime, timedelta

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_command_line_args():
    """
    解析并返回命令行参数。

    :return: 解析后的命令行参数对象
    """
    parser = argparse.ArgumentParser(description="从 WAF 获取攻击日志并发送战报", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-H', '--hour', type=int, default=1,
                        help='需要查询前多少小时的信息,与 -M 参数互斥 (default: 1)')
    parser.add_argument('-M', '--minute', type=int, default=0,
                        help='需要查询前多少分钟的信息,与 -H 参数互斥,优先级高于 -H (default: 0)')
    parser.add_argument('-r', '--round', action='store_true',
                        help='''是否开启时间取整,默认不开启,开启后会取整到小时或分钟 (default: False)
    假设现在是08:21:06.333,
    在-H 参数生效的情况下使用此参数后,当前时间为08:00:00.000,
    在-M 参数生效的情况下使用此参数后,当前时间为08:21:00.000''')
    parser.add_argument('-c', '--config', type=str, default='config/default.yaml',
                        help='配置文件路径 (default: config/default.yaml)')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    args = parser.parse_args()

    # 检查是否同时传入了 -H 和 -M 参数
    if args.hour != 1 and args.minute != 0:
        parser.error("不能同时传入 -H 和 -M 参数")

    return args

def load_config(config_path):
    """
    从指定路径加载YAML配置文件。

    :param config_path: YAML配置文件的路径
    :return: 解析后的配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            logging.debug(f"加载配置文件: {config_path}")
            decode_config = yaml.safe_load(f)
            logging.debug(f"配置文件内容: {decode_config}")
            return decode_config
    except FileNotFoundError:
        logging.error(f"配置文件未找到: {config_path}")
        exit(1)
    except yaml.YAMLError as e:
        logging.error(f"配置文件格式错误: {e}")
        exit(1)


def get_start_time(args):
    """
    根据命令行参数计算查询的开始和结束时间。

    :param args: 命令行参数对象
    :return: 一个元组，包含开始和结束的毫秒级Unix时间戳 (left_unix_time, right_unix_time)
    """
    now = datetime.now()

    if args.minute > 0:
        if args.round:
            now = now.replace(second=0, microsecond=0)
        left_time = now - timedelta(minutes=args.minute)
    else:
        if args.round:
            now = now.replace(minute=0, second=0, microsecond=0)
        left_time = now - timedelta(hours=args.hour)
    left_unix_time = int(left_time.timestamp() * 1000)
    right_unix_time = int(now.timestamp() * 1000)

    return left_unix_time, right_unix_time

def fetch_attack_records(waf_address, token, start_time, end_time, page_size=100):
    """
    从WAF API获取指定时间范围内的所有攻击记录。

    :param waf_address: WAF的管理地址
    :param token: WAF API token
    :param start_time: 查询开始的毫秒级Unix时间戳
    :param end_time: 查询结束的毫秒级Unix时间戳
    :param page_size: 每次API请求获取的记录数
    :return: 一个元组，包含攻击记录列表和总攻击次数 (block_list, total_attack_count)
    """
    api_path = "/api/open/records"
    full_path_uri = urllib.parse.urljoin(waf_address, api_path)
    query_params = {
        "page": 1,
        "page_size": page_size,
        "start": start_time,
        "end": end_time
    }
    headers = {"X-SLCE-API-TOKEN": token}

    block_list = []
    total_records = 0
    while True:
        encoded_query_params = urllib.parse.urlencode(query_params)
        parsed_uri = urllib.parse.urlparse(full_path_uri)
        full_uri = parsed_uri._replace(query=encoded_query_params).geturl()
        try:
            response = requests.get(full_uri, headers=headers, verify=False, timeout=10)
            response.raise_for_status()  # 如果请求失败则抛出HTTPError
            data = response.json()
            records = data.get('data', {}).get('data', [])
            total_records = data.get('data', {}).get('total', 0)
            block_list.extend(records)
            if len(records) < page_size:
                break
            query_params['page'] += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"请求WAF API失败 ({waf_address}): {e}")
            return [], 0

    return block_list, total_records

def get_alert_channel(config, channel_name):
    """
    根据渠道名称获取对应的告警渠道配置。

    :param config: 完整的配置字典
    :param channel_name: 渠道名称
    :return: 包含类型和具体配置的字典，如果未找到则返回 None
    """
    for channel_type, channels in config.get('alert_channels', {}).items():
        for channel in channels:
            if channel.get('name') == channel_name:
                return {
                    'type': channel_type,
                    'config': channel
                }
    return None

def send_alert(channel_name, channel_config, title, subtitle, block_list, total_attack_count):
    """
    根据渠道类型发送格式化的告警信息。

    :param channel_name: 渠道名称 (用于日志记录)
    :param channel_config: 从配置文件中获取的渠道配置
    :param title: 消息标题
    :param subtitle: 消息副标题
    :param block_list: 攻击记录列表
    :param total_attack_count: 总攻击次数
    """
    channel_type = channel_config.get('type')
    if channel_type == 'feishu':
        try:
            feishu_config = channel_config['config']
            feishu = FeiShu(feishu_config['token'], feishu_config['secret'])
            req = feishu.send_message(title, subtitle, block_list, total_attack_count)
            if req.status_code != 200:
                logging.error(f"向飞书渠道 [{channel_name}] 发送告警失败: {req.text}")
            else:
                logging.info(f"向飞书渠道 [{channel_name}] 告警发送成功")
        except KeyError as e:
            logging.error(f"飞书渠道 [{channel_name}] 配置错误，缺少键: {e}")
        except Exception as e:
            logging.error(f"发送飞书消息时发生未知错误: {e}")
    elif channel_type == 'dingtalk':
        # TODO: 实现钉钉告警
        logging.warning(f"钉钉渠道 [{channel_name}] 的告警功能尚未实现")
    else:
        logging.warning(f"不支持的告警渠道类型: {channel_type}")

def main():
    """
    主函数，编排整个脚本的执行流程。
    """
    args = get_command_line_args()
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    config = load_config(args.config)
    if not config:
        return

    start_time, end_time = get_start_time(args)
    start_dt = datetime.fromtimestamp(start_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
    end_dt = datetime.fromtimestamp(end_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"查询时间范围: {start_dt} -> {end_dt}")

    for waf in config.get('waf', []):
        waf_name = waf.get('name', '未命名WAF')
        logging.debug(f"处理WAF: {waf_name}")
        if not waf.get('alert', False):
            logging.info(f"WAF [{waf_name}] 已配置为不发送告警，跳过。")
            continue

        block_list, total_attack_count = fetch_attack_records(waf.get("address"), waf.get("token"), start_time, end_time)
        logging.info(f"WAF [{waf_name}] 在指定时间内共发现 {total_attack_count} 次攻击。")

        if total_attack_count > 0:
            title = f'{waf_name} 攻击战报'
            subtitle = f'{start_dt} 到 {end_dt}'

            for channel_name in waf.get("sendto", []):
                channel_config = get_alert_channel(config, channel_name)
                if channel_config is None:
                    logging.warning(f"未在配置文件中找到名为 [{channel_name}] 的告警渠道配置")
                    continue
                
                send_alert(channel_name, channel_config, title, subtitle, block_list, total_attack_count)
        else:
            logging.info(f"WAF [{waf_name}] 未发现攻击，无需发送战报。")


if __name__ == "__main__":
    main()