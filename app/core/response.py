from typing import Any, Optional, List, Dict

def api_response(
    data: Optional[Any] = None,
    message: str = "Success",
    status: str = "success",
    errors: Optional[List[Dict[str, Any]]] = None
) -> dict:
    """Standardizes all API responses."""
    return {
        "status": status,
        "message": message,
        "data": data,
        "errors": errors or []
    }