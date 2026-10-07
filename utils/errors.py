"""Only these sanitized messages should cross the application/UI boundary."""


class AppError(Exception):
    """An expected, safe-to-display application error."""


class ValidationError(AppError):
    pass


class DuplicateDocument(AppError):
    pass


class StorageError(AppError):
    pass


class ProviderError(AppError):
    pass
