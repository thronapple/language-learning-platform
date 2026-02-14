import hashlib
import hmac
import json
import time
from typing import Tuple


def sha256_hex(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()


def hmac_sha256(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def sign_tc3(
    service: str,
    host: str,
    region: str | None,
    action: str,
    version: str,
    secret_id: str,
    secret_key: str,
    payload: dict,
    timestamp: int | None = None,
) -> Tuple[dict, str]:
    """Return headers and canonical request string for TencentCloud TC3-HMAC-SHA256.

    See: https://www.tencentcloud.com/document/product/1278/100498
    """
    if timestamp is None:
        timestamp = int(time.time())

    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{host}\n"
    signed_headers = "content-type;host"
    payload_json = json.dumps(payload, separators=(",", ":"))
    hashed_request_payload = sha256_hex(payload_json.encode("utf-8"))
    canonical_request = (
        f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{hashed_request_payload}"
    )

    algorithm = "TC3-HMAC-SHA256"
    date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
    credential_scope = f"{date}/{service}/tc3_request"
    hashed_canonical_request = sha256_hex(canonical_request.encode("utf-8"))
    string_to_sign = (
        f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
    )

    secret_date = hmac_sha256(("TC3" + secret_key).encode("utf-8"), date)
    secret_service = hmac_sha256(secret_date, service)
    secret_signing = hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    auth = (
        f"{algorithm} Credential={secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    )

    headers = {
        "Authorization": auth,
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Version": version,
        "X-TC-Timestamp": str(timestamp),
    }
    if region:
        headers["X-TC-Region"] = region
    return headers, canonical_request

