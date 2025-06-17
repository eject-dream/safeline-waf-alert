import requests
import time
import hashlib
import base64
import hmac
import json
from retrying import retry
from src.formatters import format_report_for_feishu

class FeiShu:
    def __init__(self, token, secret):
        self.timestamp = str(int(time.time()))
        self.token = token
        self.secret = secret

    def __gen_sign(self):
        string_to_sign = '{}\n{}'.format(self.timestamp, self.secret)
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def send_message(self, title, subtitle, block_list, total_attack_count, ignore_rule=None, show_attack_ip_top=0):
        sign = self.__gen_sign()
        feishu_uri = f"https://open.feishu.cn/open-apis/bot/v2/hook/{self.token}"
        msg = format_report_for_feishu(block_list, total_attack_count, ignore_rule=ignore_rule, show_attack_ip_top=show_attack_ip_top)
        data = {
            "timestamp": self.timestamp,
            "sign": sign,
            "msg_type": "interactive",
            "card": {
                "schema": "2.0",
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "subtitle":{
                        "tag": "plain_text",
                        "content": subtitle
                    },
                    "template": "blue"
                },
                "body": {
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": msg
                        }
                    ]
                }
            }
        }

        msg = json.dumps(data)
        req = requests.post(feishu_uri, data=msg)
        return req