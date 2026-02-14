from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests
from pydantic import ValidationError

from .tc3 import sign_tc3
from ..schemas.tcb_responses import (
    TCBCommonServiceResponse,
    TCBDocumentResponse,
    TCBQueryResponse,
)
from .exceptions import ExternalServiceError

logger = logging.getLogger(__name__)


TCB_HOST = "tcb.tencentcloudapi.com"
TCB_SERVICE = "tcb"
TCB_VERSION = "2018-06-08"


class TCBClient:
    """CloudBase (TCB) HTTPS client with TC3 signing.

    Uses TencentCloud public API. Database operations are typically made via
    `CommonServiceAPI` with parameters delegating to underlying services.
    See product docs for exact payloads.
    """

    def __init__(
        self,
        env_id: str,
        secret_id: str | None = None,
        secret_key: str | None = None,
        token: str | None = None,
        region: str | None = None,
    ) -> None:
        self.env_id = env_id
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.token = token
        self.region = region

    @staticmethod
    def from_settings(settings: Any) -> "TCBClient":
        if not settings.tcb_env_id:
            raise RuntimeError("TCB_ENV_ID is required for TCB repository")
        return TCBClient(
            env_id=settings.tcb_env_id,
            secret_id=settings.tcb_secret_id,
            secret_key=settings.tcb_secret_key,
            token=settings.tcb_token,
            region=settings.tcb_region,
        )

    def _request(self, action: str, payload: dict) -> dict:
        if not self.secret_id or not self.secret_key:
            raise ExternalServiceError("TCB secret not configured", "tcb")

        try:
            headers, _ = sign_tc3(
                service=TCB_SERVICE,
                host=TCB_HOST,
                region=self.region,
                action=action,
                version=TCB_VERSION,
                secret_id=self.secret_id,
                secret_key=self.secret_key,
                payload=payload,
            )
            if self.token:
                headers["X-TC-Token"] = self.token

            url = f"https://{TCB_HOST}"
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # Parse and validate response
            try:
                response = TCBCommonServiceResponse(**data)
                return response.get_response_data()
            except ValidationError as e:
                logger.error("TCB response validation failed", extra={"error": str(e), "response": data})
                # Fallback to legacy parsing for compatibility
                if "Response" in data:
                    return data["Response"]
                return data

        except requests.RequestException as e:
            logger.error("TCB API request failed", extra={"action": action, "error": str(e)})
            raise ExternalServiceError(f"TCB API request failed: {str(e)}", "tcb")
        except Exception as e:
            logger.error("Unexpected TCB error", extra={"action": action, "error": str(e)})
            raise ExternalServiceError(f"TCB operation failed: {str(e)}", "tcb")

    # The following operations map to CommonServiceAPI calls. Adjust 'Service'/'Action'
    # and 'Data' per CloudBase database API format in your environment.
    def get_document(self, collection: str, doc_id: str) -> dict | None:
        payload = {
            "EnvId": self.env_id,
            "Service": "database",
            "Action": "QueryDocument",
            "Data": {
                "CollectionName": collection,
                "Id": doc_id,
            },
        }
        resp_data = self._request("CommonServiceAPI", payload)

        try:
            response = TCBDocumentResponse(**resp_data)
            doc = response.get_document()
            if doc and isinstance(doc, dict):
                # Ensure id field presence
                doc.setdefault("id", doc.get("_id") or doc_id)
                return doc
        except ValidationError as e:
            logger.warning(
                "TCB document response validation failed, using fallback parsing",
                extra={"error": str(e), "collection": collection, "doc_id": doc_id}
            )
            # Fallback to legacy parsing
            doc = resp_data.get("Document") or resp_data.get("Data") or resp_data.get("doc")
            if isinstance(doc, dict):
                doc.setdefault("id", doc.get("_id") or doc_id)
                return doc

        return None

    def add_document(self, collection: str, item: dict) -> str:
        payload = {
            "EnvId": self.env_id,
            "Service": "database",
            "Action": "AddDocument",
            "Data": {
                "CollectionName": collection,
                "Document": item,
            },
        }
        resp_data = self._request("CommonServiceAPI", payload)

        try:
            response = TCBDocumentResponse(**resp_data)
            inserted_id = response.get_inserted_id()
            return inserted_id or ""
        except ValidationError as e:
            logger.warning(
                "TCB add document response validation failed, using fallback parsing",
                extra={"error": str(e), "collection": collection}
            )
            # Fallback to legacy parsing - check all possible field names
            inserted_id = (
                resp_data.get("Id")
                or resp_data.get("_id")
                or resp_data.get("id")
                or (resp_data.get("InsertedIds") or [None])[0]
                or resp_data.get("DocumentId")
            )
            return str(inserted_id) if inserted_id else ""

    def delete_document(self, collection: str, doc_id: str) -> bool:
        payload = {
            "EnvId": self.env_id,
            "Service": "database",
            "Action": "DeleteDocument",
            "Data": {
                "CollectionName": collection,
                "Id": doc_id,
            },
        }
        resp_data = self._request("CommonServiceAPI", payload)

        try:
            response = TCBDocumentResponse(**resp_data)
            return response.is_deleted()
        except ValidationError as e:
            logger.warning(
                "TCB delete document response validation failed, using fallback parsing",
                extra={"error": str(e), "collection": collection, "doc_id": doc_id}
            )
            # Fallback to legacy parsing
            ok = resp_data.get("Deleted") or resp_data.get("Ok") or resp_data.get("deleted")
            return bool(ok) if ok is not None else True

    def query(self, collection: str, filters: dict | None, limit: int, offset: int) -> tuple[list[dict], int]:
        payload = {
            "EnvId": self.env_id,
            "Service": "database",
            "Action": "QueryDocuments",
            "Data": {
                "CollectionName": collection,
                "Filter": filters or {},
                "Limit": limit,
                "Offset": offset,
            },
        }
        resp_data = self._request("CommonServiceAPI", payload)

        try:
            response = TCBQueryResponse(**resp_data)
            docs = response.get_documents()
            total = response.get_total()
        except ValidationError as e:
            logger.warning(
                "TCB query response validation failed, using fallback parsing",
                extra={"error": str(e), "collection": collection}
            )
            # Fallback to legacy parsing
            docs = resp_data.get("Documents") or resp_data.get("Items") or []
            total = resp_data.get("Total") or resp_data.get("Count") or len(docs)

        # Normalize id field
        for d in docs:
            if isinstance(d, dict):
                d.setdefault("id", d.get("_id"))
        return docs, int(total)

    def query_with_date_filters(
        self,
        collection: str,
        filters: dict | None = None,
        date_filters: dict | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[dict], int]:
        """Query with enhanced filtering including date range filters."""
        # Combine filters and date filters into TCB query format
        combined_filters = filters or {}

        if date_filters:
            for field, conditions in date_filters.items():
                # Convert date conditions to TCB query format
                if "lte" in conditions:
                    # TCB uses MongoDB-style operators
                    combined_filters[field] = combined_filters.get(field, {})
                    combined_filters[field]["$lte"] = conditions["lte"]
                if "gte" in conditions:
                    combined_filters[field] = combined_filters.get(field, {})
                    combined_filters[field]["$gte"] = conditions["gte"]

        payload = {
            "EnvId": self.env_id,
            "Service": "database",
            "Action": "QueryDocuments",
            "Data": {
                "CollectionName": collection,
                "Filter": combined_filters,
                "Limit": limit,
                "Offset": offset,
            },
        }
        resp_data = self._request("CommonServiceAPI", payload)

        try:
            response = TCBQueryResponse(**resp_data)
            docs = response.get_documents()
            total = response.get_total()
        except ValidationError as e:
            logger.warning(
                "TCB query with date filters response validation failed, using fallback parsing",
                extra={"error": str(e), "collection": collection}
            )
            # Fallback to legacy parsing
            docs = resp_data.get("Documents") or resp_data.get("Items") or []
            total = resp_data.get("Total") or resp_data.get("Count") or len(docs)

        # Normalize id field
        for d in docs:
            if isinstance(d, dict):
                d.setdefault("id", d.get("_id"))
        return docs, int(total)
