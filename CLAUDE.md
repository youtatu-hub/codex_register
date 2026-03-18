# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 Python 的 OpenAI Codex 账号自动注册工具，通过直接调用 OpenAI 认证接口完成注册流程，无需浏览器。使用 curl_cffi 模拟浏览器指纹，通过 MailAPI 获取邮箱验证码。

## 核心命令

### 运行注册
```bash
# 默认配置（5个账号，单线程）
python codex_register.py

# 指定数量和并发
python codex_register.py --count 20 --workers 5
```

### 安装依赖
```bash
pip install -r requirements.txt
```

## 架构说明

### 核心流程（codex_register.py）

1. **OAuth 授权流程**：使用 PKCE 方式发起 OAuth 授权（`create_oauth_params`）
2. **Sentinel 反机器人**：获取 OpenAI Sentinel token 绕过机器人检测
3. **邮箱提交与 OTP**：提交邮箱地址，区分新账号/已注册账号的不同处理路径
4. **验证码轮询**：通过 MailAPI 轮询获取 6 位验证码（`poll_verification_code`）
5. **账号创建**：新账号需要设置密码、姓名、生日
6. **Token 兑换**：通过 authorization_code 兑换 access_token 和 refresh_token

### 浏览器指纹伪装（APISession）

- 使用 `curl_cffi` 库模拟真实浏览器的 TLS 指纹和 HTTP/2 特征
- 随机选择浏览器 profile（Chrome/Safari/Firefox/Edge 多版本）
- 随机 Accept-Language 头（支持多语言环境）
- 每个会话独立指纹，避免被识别为自动化工具

### 代理池机制

- 从 `proxy_cache.json` 加载代理列表
- 支持 http/socks4/socks5 协议（优先级：socks5 > socks4 > http）
- 每次注册随机选择代理（`pick_random_proxy`）
- 失败重试时会更换代理

### MailAPI 集成（mailapi.py）

- 封装 cloudflare_temp_email 邮件服务接口
- 轮询查询邮件并提取 OpenAI 发送的 6 位验证码
- 支持自动重发 OTP（每 25 秒）
- 超时时间 180 秒

### 并发控制

- 使用 `ThreadPoolExecutor` 实现多线程并发
- 同一波次内错开启动（1-2.5秒随机延迟）
- 线程安全的统计计数（使用 threading.Lock）

## 配置文件

### .env 必需字段
- `MAIL_API_URL`：邮件查询服务地址
- `MAIL_API_AUTH`：邮件服务管理密码
- `EMAIL_DOMAINS`：随机邮箱域名池（逗号分隔）

### .env 可选字段
- `CPA_URL`：token 上传服务器地址
- `MANAGEMENT_KEY`：上传服务器认证密钥
- `MAIL_PASSWD`：cloudflare_temp_email 私有站点密码

## 输出文件

- `tokens/<email>--<password>.json`：注册成功的账号信息（包含 access_token、refresh_token、id_token）
- `codex_register.log`：详细运行日志
- `proxy_cache.json`：代理池缓存（需手动维护或通过外部脚本生成）

## 重要常量

- `MAX_RETRY_PER_ACCOUNT = 5`：单账号最大重试次数
- `MAIL_POLL_TIMEOUT = 180`：验证码轮询超时（秒）
- `OTP_RESEND_INTERVAL = 25`：OTP 重发间隔（秒）
- `LOCAL_CALLBACK_PORT = 1455`：OAuth 回调端口

## 注意事项

- 代码使用 Windows 非法文件名处理（文件名中的 `--` 分隔邮箱和密码）
- 已注册账号在提交邮箱时会自动发送 OTP，无需手动触发
- 密码生成规则：5个字母 + 6个数字 + 1个符号，随机打乱
- 姓名和生日随机生成（18-40岁之间）
