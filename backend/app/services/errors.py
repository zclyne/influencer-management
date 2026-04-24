class ServiceError(Exception):
    code = "service_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
