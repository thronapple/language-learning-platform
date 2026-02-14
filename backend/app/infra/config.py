import os


class Settings:
    def __init__(self) -> None:
        self.env: str = os.getenv("ENV", "dev")
        self.pay_enabled: bool = os.getenv("PAY_ENABLED", "false").lower() == "true"
        self.ads_enabled: bool = os.getenv("ADS_ENABLED", "true").lower() == "true"
        flags = os.getenv("FEATURE_FLAGS", "").strip()
        self.feature_flags: list[str] = [f.strip() for f in flags.split(",") if f.strip()] if flags else []
        # Repository provider: memory | tcb
        self.repo_provider: str = os.getenv("REPO_PROVIDER", "memory").lower()
        # CloudBase credentials (if using TCB repo)
        self.tcb_env_id: str | None = os.getenv("TCB_ENV_ID")
        self.tcb_region: str | None = os.getenv("TCB_REGION")
        self.tcb_secret_id: str | None = os.getenv("TCB_SECRET_ID")
        self.tcb_secret_key: str | None = os.getenv("TCB_SECRET_KEY")
        self.tcb_token: str | None = os.getenv("TCB_TOKEN")
        # Import whitelist domains (comma separated)
        wl = os.getenv("IMPORT_WHITELIST", "example.com")
        self.import_whitelist: list[str] = [d.strip().lower() for d in wl.split(",") if d.strip()]
        # WeChat auth
        self.wechat_auth_enabled: bool = os.getenv("WECHAT_AUTH_ENABLED", "false").lower() == "true"
        self.wechat_appid: str | None = os.getenv("WECHAT_APPID")
        self.wechat_secret: str | None = os.getenv("WECHAT_SECRET")
        self.wechat_mock_prefix: str = os.getenv("WECHAT_MOCK_PREFIX", "mock_")
        # Storage
        self.storage_provider: str = os.getenv("STORAGE_PROVIDER", "local").lower()
        self.cdn_base: str | None = os.getenv("CDN_BASE")
        # COS (Cloud Object Storage)
        self.cos_bucket: str | None = os.getenv("COS_BUCKET")
        self.cos_region: str | None = os.getenv("COS_REGION")
        self.cos_secret_id: str | None = os.getenv("COS_SECRET_ID")
        self.cos_secret_key: str | None = os.getenv("COS_SECRET_KEY")
        self.cos_cdn_base: str | None = os.getenv("COS_CDN_BASE")


settings = Settings()
