from __future__ import annotations

from typing import Any, Optional, Dict
import requests
import logging
import time

logger = logging.getLogger(__name__)


class WeChatAuthClient:
    """Minimal WeChat jscode2session client.

    Docs: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
    """

    def __init__(self, appid: str, secret: str, timeout: float = 5.0) -> None:
        self.appid = appid
        self.secret = secret
        self.timeout = timeout

    @staticmethod
    def from_settings(settings: Any) -> "WeChatAuthClient":
        if not settings.wechat_appid or not settings.wechat_secret:
            raise RuntimeError("WECHAT_APPID/WECHAT_SECRET are required when auth enabled")
        return WeChatAuthClient(settings.wechat_appid, settings.wechat_secret)

    def exchange_code(self, code: str) -> dict:
        """Return response dict. On success, contains 'openid'."""
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": self.appid,
            "secret": self.secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        resp = requests.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data


class WeChatClient:
    """WeChat API client for template messages and other features.

    Docs: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-message-management/subscribe-message/sendMessage.html
    """

    def __init__(self, appid: str, secret: str, timeout: float = 10.0) -> None:
        self.appid = appid
        self.secret = secret
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    @staticmethod
    def from_settings(settings: Any) -> "WeChatClient":
        if not settings.wechat_appid or not settings.wechat_secret:
            raise RuntimeError("WECHAT_APPID/WECHAT_SECRET are required")
        return WeChatClient(settings.wechat_appid, settings.wechat_secret)

    def _get_access_token(self) -> str:
        """Get or refresh access token."""
        # Check if cached token is still valid
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        # Request new token
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.secret
        }

        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if "access_token" in data:
                self._access_token = data["access_token"]
                # Token expires in 7200 seconds, refresh 5 minutes early
                self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300
                logger.info("WeChat access token refreshed")
                return self._access_token
            else:
                error_msg = data.get("errmsg", "Unknown error")
                logger.error(f"Failed to get access token: {error_msg}")
                raise RuntimeError(f"WeChat API error: {error_msg}")

        except requests.RequestException as e:
            logger.error(f"Failed to request access token: {e}")
            raise

    def send_template_message(
        self,
        openid: str,
        template_id: str,
        data: Dict[str, Dict[str, str]],
        page: Optional[str] = None,
        miniprogram_state: str = "formal"
    ) -> dict:
        """
        Send template/subscribe message to user.

        Args:
            openid: User's openid
            template_id: Template ID from WeChat MP platform
            data: Template data, e.g., {"thing1": {"value": "标题"}, "number2": {"value": "5"}}
            page: Mini program page to navigate to
            miniprogram_state: "formal" | "trial" | "developer"

        Returns:
            Response from WeChat API

        Docs: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/mp-message-management/subscribe-message/sendMessage.html
        """
        access_token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"

        payload = {
            "touser": openid,
            "template_id": template_id,
            "data": data,
            "miniprogram_state": miniprogram_state
        }

        if page:
            payload["page"] = page

        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            result = resp.json()

            if result.get("errcode") == 0:
                logger.info(
                    "Template message sent successfully",
                    extra={"openid": openid[:10] + "***", "template_id": template_id}
                )
            else:
                logger.warning(
                    "Template message failed",
                    extra={
                        "openid": openid[:10] + "***",
                        "errcode": result.get("errcode"),
                        "errmsg": result.get("errmsg")
                    }
                )

            return result

        except requests.RequestException as e:
            logger.error(f"Failed to send template message: {e}")
            raise

