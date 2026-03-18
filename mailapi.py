import re
import requests


class MailAPI:
    def __init__(
        self,
        worker_url: str,
        admin_auth: str,
        webmail_password: str = "",
        site_url: str = "",
    ):
        self.base_url = worker_url.rstrip("/")
        self.urls = [
            self.base_url + "/admin/mails",
            self.base_url + "/mails",
        ]
        self.headers = {
            "x-admin-auth": admin_auth
        }

        # 可选的 Webmail 认证头，仅在传入时附加
        if webmail_password:
            self.headers["x-custom-auth"] = webmail_password
        if site_url:
            origin = site_url.rstrip("/")
            self.headers["Origin"] = origin
            self.headers["Referer"] = origin + "/"

    def get_mails(self, limit=1, offset=0, address=None):
        params = {
            "limit": limit,
            "offset": offset
        }

        if address:
            params["address"] = address

        last_error = None
        for url in self.urls:
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=30)
                resp.raise_for_status()

                content_type = resp.headers.get("Content-Type", "")
                try:
                    data = resp.json()
                except ValueError as exc:
                    snippet = resp.text.strip().replace("\r", " ").replace("\n", " ")
                    snippet = snippet[:180]
                    raise RuntimeError(
                        f"MailAPI 接口 {url} 返回的不是 JSON，"
                        f"status={resp.status_code}, content_type={content_type!r}, body={snippet!r}"
                    ) from exc

                if not isinstance(data, dict) or "results" not in data:
                    raise RuntimeError(
                        f"MailAPI 接口 {url} 返回结构异常，"
                        f"status={resp.status_code}, content_type={content_type!r}, type={type(data).__name__}"
                    )

                return data
            except Exception as exc:
                last_error = exc

        raise RuntimeError(f"MailAPI 所有候选接口都失败了: {last_error}")

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
