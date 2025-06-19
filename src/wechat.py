import requests
import json
import logging
from src.formatters import format_report_for_wechat

class WeChat:
    def __init__(self, token):
        self.token = token

    def send_message(self, title, subtitle, block_list, total_attack_count, ignore_rule=None, show_attack_ip_top=0):
        wechat_uri = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={self.token}"
        msg = format_report_for_wechat(block_list, total_attack_count, ignore_rule=ignore_rule, show_attack_ip_top=show_attack_ip_top)
        data = {
            "msgtype": "markdown_v2",
            "markdown_v2": {
                "content": f"### {title} \n #### {subtitle} \n {msg}"
            }
        }
        alert_msg = json.dumps(data)
        logging.debug(f"本次请求数据为: {alert_msg}")
        req = requests.post(wechat_uri, data=alert_msg, headers={"Content-Type": "application/json"})
        logging.debug(f"本次请求返回为: {req.text}")
        return req