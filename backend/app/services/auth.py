import logging
from ..schemas.auth import User
from ..repositories.interfaces import Repository
from ..infra.config import settings
from ..infra.wechat_client import WeChatAuthClient
from ..infra.exceptions import ExternalServiceError, AuthenticationError

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, repo: Repository, wechat: WeChatAuthClient | None = None) -> None:
        self.repo = repo
        self.wechat = wechat

    def exchange_code_for_openid(self, code: str) -> str:
        # Prefer WeChat API when a client is provided
        if self.wechat:
            try:
                data = self.wechat.exchange_code(code)
                openid = data.get("openid")
                if openid:
                    logger.info("Successfully exchanged WeChat code for openid", extra={"code_suffix": code[-6:]})
                    return openid
                else:
                    logger.warning("WeChat API returned no openid", extra={"response": data})
                    raise ExternalServiceError("WeChat API returned invalid response", "wechat")
            except Exception as e:
                logger.error("WeChat API call failed", extra={"error": str(e), "code_suffix": code[-6:]})
                if settings.wechat_mock_prefix:
                    # Only fall back to mock if explicitly configured
                    logger.info("Falling back to mock authentication")
                else:
                    raise ExternalServiceError("WeChat authentication unavailable", "wechat")

        # Mock authentication (development/testing only)
        if not settings.wechat_mock_prefix:
            raise AuthenticationError("WeChat authentication required but not available")

        prefix = settings.wechat_mock_prefix
        suffix = code[-6:] if code else "anon"
        mock_openid = f"{prefix}{suffix}"
        logger.info("Using mock authentication", extra={"mock_openid": mock_openid})
        return mock_openid

    def get_or_create_user(self, openid: str) -> User:
        # Try find by openid
        items, total = self.repo.query("users", {"openid": openid}, limit=1, offset=0)
        if total:
            doc = items[0]
            return User(**doc)
        # Create minimal user profile
        doc = {"openid": openid, "nick": "Guest", "avatar": "", "pro_until": None}
        self.repo.put("users", doc)
        return User(**doc)
