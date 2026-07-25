from fastapi import HTTPException, status

class SaleszyException(HTTPException):
    """Base exception for Saleszy v2"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)

class BusinessRuleException(SaleszyException):
    """Used when a business rule is violated (e.g., duplicate SKU, negative stock)"""
    pass

class InventoryException(SaleszyException):
    """Used for inventory-related failures with optional structured data."""

    def __init__(
        self,
        detail: str,
        *,
        code: str = "INVENTORY_ERROR",
        product_id: str | None = None,
        selling_unit_id: str | None = None,
        product_name: str | None = None,
        selling_unit_name: str | None = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(detail=detail, status_code=status_code)

        self.code = code
        self.product_id = product_id
        self.selling_unit_id = selling_unit_id
        self.product_name = product_name
        self.selling_unit_name = selling_unit_name

class AuthorizationException(SaleszyException):
    """Used when a user tries to perform an unauthorized action"""
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)