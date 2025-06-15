# 槽

官方的好用吗？

# WAF 攻击告警脚本

这是一套用于从长亭雷池 WAF 中获取指定时间段内的攻击日志，并将汇总后的“攻击战报”发送到指定的告警渠道（目前支持飞书/钉钉）。

## 功能特性

-   **数据拉取**：通过 WAF 的开放 API 拉取攻击记录。
-   **时间自定义**：支持查询过去N小时或N分钟的日志。
-   **时间取整**：可将查询的开始和结束时间进行取整，便于定时任务执行。
-   **多渠道告警**：支持将报告发送到多个飞书群组。
-   **灵活配置**：通过 `YAML` 文件管理所有 WAF 实例和告警渠道，易于扩展。
-   **调试模式**：提供 `--debug` 选项，输出详细的执行日志，方便排查问题。

## 安装

1.  克隆或下载本仓库到您的本地。
2.  安装所需的 Python 依赖库。建议使用虚拟环境。

    ```bash
    pip install -r requirements.txt
    ```

## 配置

首先，查看官方文档，获取waf token。
[获取token](https://help.waf-ce.chaitin.cn/node/01973fc6-e25e-7eda-8ea8-dae97bdd4213)

所有配置均在 `config/default.yaml` 文件中定义。您可以复制该文件并重命名（例如 `my_config.yaml`）来进行个性化配置。

### 配置文件示例 (`config/default.yaml`)

```yaml
# WAF 实例列表
waf:
  - name: "官网WAF"  # WAF实例的友好名称
    address: "https://192.168.1.1:9443" # WAF的管理地址
    token: "your-api-token-here" # 从WAF获取的API Token
    alert: true # 是否为该WAF实例发送告警
    sendto: # 告警渠道列表，对应下方 alert_channels 中定义的名称
      - "安全部-飞书群"
      - "研发部-飞书群"

# 告警渠道配置
alert_channels:
  # 飞书机器人列表
  feishu:
    - name: "安全部-飞书群" # 渠道的唯一名称
      token: "your-feishu-bot-token-1" # 飞书机器人的Webhook Token
      secret: "your-feishu-bot-secret-1" # 飞书机器人的签名密钥

    - name: "研发部-飞书群"
      token: "your-feishu-bot-token-2"
      secret: "your-feishu-bot-secret-2"

  # 钉钉机器人列表
  dingtalk:
    - name: "钉钉测试群"
      token: "your-dingtalk-bot-token"
      secret: "your-dingtalk-bot-secret"
```

## 使用方法

### 安装

当前已使用 `uv` 进行项目管理，git clone 项目后，直接运行 `uv venv` 创建虚拟环境，然后运行 `uv sync` 安装依赖即可。

### 运行

通过命令行运行 `python main.py --help` 查看帮助信息。

### 命令行参数

-   `-H, --hour`：查询过去多少小时的日志（默认: 1）。
-   `-M, --minute`：查询过去多少分钟的日志。此参数优先级高于 `--hour`。
-   `-r, --round`：是否对时间进行取整。
-   `-c, --config`：指定配置文件的路径（默认: `config/default.yaml`）。
-   `--debug`：开启调试模式，输出更详细的日志。

### 使用示例

-   **默认运行** (查询过去1小时的日志):
    ```bash
    python main.py
    ```

-   **查询过去30分钟的日志**:
    ```bash
    python main.py -M 30
    ```

-   **查询过去2小时的日志，并对时间进行取整**:
    ```bash
    python main.py -H 2 -r
    ```

-   **使用自定义配置文件并开启调试模式**:
    ```bash
    python main.py -c config/my_config.yaml --debug
    ```

## 待办事项 (TODO)

-   [X] 实现钉钉告警渠道的发送逻辑。
-   [X] 使用UV进行项目管理.
-   [ ] 基于syslog实现实时波动告警。

~~-   [ ] 实现微信告警渠道的发送逻辑。（我没有微信机器人，所以大概率不会写了吧）~~