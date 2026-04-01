class BillingError(Exception):
    """Base billing domain error."""


class BillingNotFoundError(BillingError):
    """Raised when a billing resource is missing."""


class BillingValidationError(BillingError):
    """Raised when request or transition is invalid."""
