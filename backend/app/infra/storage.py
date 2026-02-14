from __future__ import annotations

import os
from typing import Any


class StorageClient:
    def upload_file(self, local_path: str, remote_path: str) -> str:  # returns URL
        raise NotImplementedError


class LocalStorage(StorageClient):
    def __init__(self, cdn_base: str | None = None) -> None:
        self.cdn_base = cdn_base.rstrip("/") if cdn_base else None

    def upload_file(self, local_path: str, remote_path: str) -> str:
        if self.cdn_base:
            return f"{self.cdn_base}/{remote_path}"
        # In local dev without CDN, return a stable forward-slash path
        # so tests are OS-agnostic and URLs look consistent.
        return remote_path


class COSStorage(StorageClient):
    def __init__(self, bucket: str, region: str, secret_id: str, secret_key: str, cdn_base: str | None = None) -> None:
        self.bucket = bucket
        self.region = region
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.cdn_base = cdn_base.rstrip("/") if cdn_base else None

    def upload_file(self, local_path: str, remote_path: str) -> str:
        # Lazy import to avoid hard dependency in local dev
        try:
            from qcloud_cos import CosConfig, CosS3Client  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("COS SDK not installed: pip install cos-python-sdk-v5") from e

        config = CosConfig(Region=self.region, SecretId=self.secret_id, SecretKey=self.secret_key)
        client = CosS3Client(config)
        with open(local_path, "rb") as fp:
            client.put_object(Bucket=self.bucket, Body=fp, Key=remote_path)

        if self.cdn_base:
            return f"{self.cdn_base}/{remote_path}"
        # Default COS public URL shape (ensure your bucket/ACL allows access)
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{remote_path}"
