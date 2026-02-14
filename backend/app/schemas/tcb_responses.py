"""
Pydantic models for TencentCloud CloudBase (TCB) API responses.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TCBError(BaseModel):
    """TCB API error response."""
    Code: str
    Message: str


class TCBDocumentResponse(BaseModel):
    """Response for document operations (get, add, delete)."""
    model_config = {"populate_by_name": True, "extra": "allow"}  # Allow both field name and alias

    # Different response formats across environments
    Document: Optional[Dict[str, Any]] = None
    Data: Optional[Dict[str, Any]] = None
    doc: Optional[Dict[str, Any]] = None

    # For add operations
    Id: Optional[str] = None
    id_underscore: Optional[str] = Field(None, alias="_id")  # MongoDB-style _id field
    InsertedIds: Optional[List[str]] = None
    DocumentId: Optional[str] = None

    # For delete operations
    Deleted: Optional[bool] = None
    Ok: Optional[bool] = None
    deleted: Optional[bool] = None

    Error: Optional[TCBError] = None

    def get_document(self) -> Optional[Dict[str, Any]]:
        """Extract document from various possible response fields."""
        return self.Document or self.Data or self.doc

    def get_inserted_id(self) -> Optional[str]:
        """Extract inserted document ID from various possible response fields."""
        return (
            self.Id or
            self.id_underscore or
            (self.InsertedIds[0] if self.InsertedIds else None) or
            self.DocumentId
        )

    def is_deleted(self) -> bool:
        """Check if delete operation was successful."""
        return bool(self.Deleted or self.Ok or self.deleted)


class TCBQueryResponse(BaseModel):
    """Response for query operations."""
    # Document lists
    Documents: Optional[List[Dict[str, Any]]] = None
    Items: Optional[List[Dict[str, Any]]] = None

    # Total counts
    Total: Optional[int] = None
    Count: Optional[int] = None

    Error: Optional[TCBError] = None

    def get_documents(self) -> List[Dict[str, Any]]:
        """Extract documents from various possible response fields."""
        return self.Documents or self.Items or []

    def get_total(self, fallback_to_length: bool = True) -> int:
        """Extract total count from response."""
        total = self.Total or self.Count
        if total is not None:
            return total

        if fallback_to_length:
            return len(self.get_documents())

        return 0


class TCBCommonServiceResponse(BaseModel):
    """Wrapper for CommonServiceAPI responses."""
    Response: Optional[Dict[str, Any]] = None
    Error: Optional[TCBError] = None

    def get_response_data(self) -> Dict[str, Any]:
        """Extract the actual response data."""
        if self.Error:
            raise ValueError(f"TCB API Error: {self.Error.Code} - {self.Error.Message}")

        return self.Response or {}