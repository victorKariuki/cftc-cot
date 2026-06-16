class COTError(Exception):
    """Base exception for all CFTC COT SDK errors."""
    pass

class COTQueryError(COTError):
    """Raised when a query is invalid or returns a 400 error."""
    pass

class COTConnectionError(COTError):
    """Raised for network issues, 403, or timeouts."""
    pass

class COTClassificationError(COTError):
    """Raised when an operation is invalid for the dataset classification."""
    pass

class COTDataError(COTError):
    """Raised for empty results or data parsing issues."""
    pass
