import requests
import re


class MailAPI:
    def __init__(self, worker_url: str, admin_auth: str, webmail_password: str = ""):
        self.url = worker_url.rstrip("/") + "/admin/mails"
        self.headers = {
            "x-admin-auth": admin_auth
        }

        # 可选的 Webmail 认证头，仅在传入时附加
        if webmail_password:
            self.headers["x-custom-auth"] = webmail_password

    def get_mails(self, limit=1, offset=0, address=None):
        params = {
            "limit": limit,
            "offset": offset
        }

        if address:
            params["address"] = address

        resp = requests.get(self.url, headers=self.headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_latest_code(self, address=None):
        data = self.get_mails(limit=1, offset=0, address=address)

        if not data["results"]:
            return None

        raw = data["results"][0]["raw"]
        # print("邮件内容:", raw)

        # 优先级 1：精准上下文匹配 (支持 "code is 580658", "Code: 580658", 忽略大小写)
        # (?i) 忽略大小写
        # (?:code[\s:]*(?:is\s*)?) 匹配 "code is ", "code: ", "code " 等前缀
        match = re.search(r"(?i)(?:code[\s:]*(?:is\s*)?)(\d{6})\b", raw)
        if match:
            return match.group(1) # 注意这里用 group(1) 提取括号内的纯数字

        # 优先级 2：宽泛上下文匹配（匹配标题或正文附近的 ChatGPT 验证码）
        match = re.search(r"(?i)(?:chatgpt|openai|verification)[\s\S]{0,30}?\b(\d{6})\b", raw)
        if match:
            return match.group(1)

        # 优先级 3：兜底匹配（原逻辑升级版）
        # (?<!#) 是负向零宽断言，防止匹配到 HTML 颜色代码例如 #123456
        # (?<!\d) 和 (?!\d) 确保它严格只是 6 位，前后没有连着的数字
        match = re.search(r"(?<!#)(?<!\d)\b\d{6}\b(?!\d)", raw)
        if match:
            return match.group(0)

        return None


if __name__ == "__main__":
    api = MailAPI(
        worker_url="https://xxxxxxxxxxx",
        admin_auth="xxxxxx"
    )

    code = api.get_latest_code("xxxxxxxx@xxxx.xxx")

    print("验证码:", code)
