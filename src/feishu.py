import requests
import time
import hashlib
import base64
import hmac
import json
from retrying import retry
from collections import Counter
from src.waf_module_dict import MODULE_DICT
from src.library import is_not_ip_address

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

    # 格式化输出
    def format_report(self, block_list, total_attack_count):
        host_counts = Counter(json_obj.get('host') for json_obj in block_list if is_not_ip_address(json_obj.get('host')))
        msg = ""
        for host, count in host_counts.items():
            msg += f"\n---\n站点：{host}， 总攻击次数：{count}"
            filtered_list = [
                MODULE_DICT.get(module_or_policy := (json_obj.get('policy_name') or json_obj.get('module')), module_or_policy)
                for json_obj in block_list
                if json_obj.get('host') == host and json_obj.get('attack_type') != -2
            ]
            attack_reason = Counter(filtered_list)
            attack_reason_text = '\n'.join(f'  - {k}: {v}' for k, v in attack_reason.items())
            whitelist_reason = Counter(
                json_obj.get('policy_name') for json_obj in block_list 
                if json_obj.get('host') == host and json_obj.get('attack_type') == -2
            )
            whitelist_reason_text = '\n'.join(f'  - {k}: {v}' for k, v in whitelist_reason.items())
            msg += f'\n- 攻击拦截原因：\n{attack_reason_text}'
            if whitelist_reason:
                msg += f'\n- 白名单原因：\n{whitelist_reason_text}'
        msg += f'\n---\n**总阻断次数：{total_attack_count}**'
        return msg


    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def send_message(self, title, subtitle, msg):
        sign = self.__gen_sign()
        feishu_uri = f"https://open.feishu.cn/open-apis/bot/v2/hook/{self.token}"
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