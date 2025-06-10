from collections import Counter
from src.library import is_not_ip_address
from src.waf_module_dict import MODULE_DICT

def format_report_for_feishu(block_list, total_attack_count):
    """
    将攻击报告格式化为飞书Markdown格式
    """
    msg = ""
    host_counts = Counter(json_obj.get('host') for json_obj in block_list if is_not_ip_address(json_obj.get('host')))
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
