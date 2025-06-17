import socket
import logging
from syslog_rfc5424_parser import SyslogMessage, ParseError
import json

def start_syslog_server(listen_ip, listen_port, handle_log_func):
    """
    启动 syslog UDP 服务器，收到日志后调用 handle_log_func(parsed_json, raw_msg)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_ip, listen_port))
    logging.info(f"Syslog server listening on {listen_ip}:{listen_port}")
    while True:
        data, _ = sock.recvfrom(65535)
        try:
            msg = SyslogMessage.parse(data.decode(errors='ignore'))
            # 雷池日志体在 msg.msg 里
            try:
                parsed_json = json.loads(msg.msg)
                handle_log_func(parsed_json, msg)
            except Exception as e:
                logging.warning(f"日志 JSON 解析失败: {e}, 原始内容: {msg.msg}")
        except ParseError as e:
            logging.warning(f"Syslog 解析失败: {e}, 原始内容: {data}")
