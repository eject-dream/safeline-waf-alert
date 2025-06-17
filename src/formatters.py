from collections import Counter
from src.library import is_not_ip_address
from src.waf_module_dict import MODULE_DICT


def format_report_for_feishu(block_list, total_attack_count, ignore_rule=None, show_attack_ip_top=0):
    """
    将攻击报告格式化为飞书Markdown格式，支持 ignore_rule 过滤
    :param block_list: 攻击记录列表
    :param total_attack_count: 总攻击次数
    :param ignore_rule: 需要忽略的规则名列表（policy_name/module），可为 None
    :param show_attack_ip_top: 需要显示的攻击 IP 个数，0 表示不显示
    """
    if ignore_rule is None:
        ignore_rule = set()
    else:
        ignore_rule = set(ignore_rule)

    # 过滤掉 ignore_rule 里的记录
    def is_not_ignored(json_obj):
        policy_or_module = json_obj.get('policy_name') or json_obj.get('module')
        return policy_or_module not in ignore_rule

    filtered_block_list = [j for j in block_list if is_not_ignored(j)]
    msg = ""
    host_counts = Counter(json_obj.get('host') for json_obj in filtered_block_list if is_not_ip_address(json_obj.get('host')))
    for host, count in host_counts.items():
        msg += f"\n---\n站点：{host}， 总攻击次数：{count}"
        filtered_list = [
            MODULE_DICT.get(module_or_policy := (json_obj.get('policy_name') or json_obj.get('module')), module_or_policy)
            for json_obj in filtered_block_list
            if json_obj.get('host') == host and json_obj.get('attack_type') != -2
        ]
        attack_reason = Counter(filtered_list)
        attack_reason_text = '\n'.join(f'  - {k}: {v}' for k, v in attack_reason.items())
        whitelist_reason = Counter(
            json_obj.get('policy_name') for json_obj in filtered_block_list 
            if json_obj.get('host') == host and json_obj.get('attack_type') == -2
        )
        whitelist_reason_text = '\n'.join(f'  - {k}: {v}' for k, v in whitelist_reason.items())
        msg += f'\n- 攻击拦截原因：\n{attack_reason_text}'
        if whitelist_reason:
            msg += f'\n- 白名单原因：\n{whitelist_reason_text}'
        if show_attack_ip_top > 0:
            attack_ip = Counter(json_obj.get('src_ip') for json_obj in filtered_block_list)
            attack_ip_text = '\n'.join(f'  - {k}: {v}' for k, v in attack_ip.items())
            msg += f'\n---\n 攻击IP & 次数：\n{attack_ip_text}'
    msg += f'\n---\n**总阻断次数：{total_attack_count}**'
    return msg

# 经测试，钉钉的Markdown格式与飞书的Markdown格式相同，因此可以共用
def format_report_for_dingtalk(block_list, total_attack_count, ignore_rule=None, show_attack_ip_top=0):
    """
    太好啦，钉钉的Markdown格式与飞书的Markdown格式相同，因此可以共用（偷懒真好，bushi）
    """
    return format_report_for_feishu(block_list, total_attack_count, ignore_rule=ignore_rule, show_attack_ip_top=show_attack_ip_top)
