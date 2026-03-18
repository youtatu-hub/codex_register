# Repository Guidelines

## 项目结构与模块组织
核心脚本在 `codex_register.py`，负责注册主流程、并发控制、验证码轮询、结果保存与上传。`mailapi.py` 提供 MailAPI 封装，`requirements.txt` 记录依赖，`proxy_cache.json` 是可选代理缓存，`ss.py` 为片段草稿文件（不参与主流程）。运行时会生成 `tokens/`（结果文件）与 `codex_register.log`（日志）。如需扩展功能，优先在 `codex_register.py` 中按功能区块添加，避免散落到新文件。

## 构建、测试与本地运行命令
- 安装依赖：`pip install -r requirements.txt`，安装 `curl_cffi`、`requests`、`PySocks`。
- 运行主流程：`python codex_register.py`，可加 `--count` 与 `--workers` 控制批量与并发。
- 当前命令行参数仅包含 `--count` 与 `--workers`；代理通过 `proxy_cache.json` 提供。
- 示例：`python codex_register.py --count 5 --workers 2`。
本仓库无构建产物与打包脚本，主要通过脚本直运行。

## 代码风格与命名约定
使用 Python 3.10+，缩进 4 空格。常量使用全大写下划线（如 `OAI_AUTH_URL`），函数/变量使用 `snake_case`。保持现有“功能分区块”风格（带分隔注释），新逻辑请靠近相关区块，避免大段重复。

## 测试指南
当前未包含自动化测试与测试框架。改动后请至少用小样本手动验证主流程（例如 `--count 1 --workers 1`），并检查 `codex_register.log` 与 `tokens/` 输出是否符合预期（结果文件命名为 `tokens/<email>--<password>.json`）。若新增测试目录，请使用清晰的命名（如 `test_*.py`）。

## 提交与 PR 规范
历史提交以简短动词开头（如 `Update README.md`），偶有中文说明（如修复类提交）。建议保持简洁、描述清晰，必要时注明影响范围。PR 请包含：变更摘要、运行方式/命令、配置改动说明；若涉及外部服务或代理，注明测试环境与注意事项。

## 安全与配置提示
配置常量集中在 `codex_register.py`，请避免提交真实密钥、邮箱域名池或内部服务地址。涉及 `MAIL_API_AUTH`、`MANAGEMENT_KEY` 等敏感值时，使用占位符并在 PR 描述中说明需要的本地配置步骤。`MAIL_PASSWD` 仅在初始化 `MailAPI` 时通过 `webmail_password` 传入后才会生效。
