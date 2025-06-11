import logging
import requests
import time
import hashlib
import base64
import hmac
import json
import urllib
from retrying import retry
from src.formatters import format_report_for_dingtalk

class DingTalk:
    def __init__(self, token, secret):
        self.timestamp = str(round(time.time() * 1000))
        self.token = token
        self.secret = secret

    def __gen_sign(self):
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(self.timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def send_message(self, title, subtitle, block_list, total_attack_count):
        sign = self.__gen_sign()
        dingtalk_uri = f"https://oapi.dingtalk.com/robot/send?access_token={self.token}&timestamp={self.timestamp}&sign={sign}"
        msg = format_report_for_dingtalk(block_list, total_attack_count)
        logging.debug(f"本次请求消息为: {msg}")
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title":title,
                "text": f"### {title} \n #### {subtitle} \n > {msg}"
            },
            "at": {
                "atMobiles": [],
                "atUserIds": [],
                "isAtAll": False
            }
        }
        logging.debug(f"本次请求内容为: {data}")
        alert_msg = json.dumps(data)
        logging.debug(f"本次请求数据为: {alert_msg}")
        req = requests.post(dingtalk_uri, data=alert_msg, headers={"Content-Type": "application/json"})
        logging.debug(f"本次请求返回为: {req.text}")
        return req