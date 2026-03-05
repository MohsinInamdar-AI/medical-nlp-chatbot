from fastapi import HTTPException, status

def http_error(code: str, message: str, http_status: int, mrd_number: str | None = None) -> HTTPException:
    payload = {"error": message, "code": code, "mrd_number": mrd_number}
    return HTTPException(status_code=http_status, detail=payload)

def bad_request(code: str, message: str, mrd_number: str | None = None) -> HTTPException:
    return http_error(code, message, status.HTTP_400_BAD_REQUEST, mrd_number)

def not_found(code: str, message: str, mrd_number: str | None = None) -> HTTPException:
    return http_error(code, message, status.HTTP_404_NOT_FOUND, mrd_number)

def server_error(code: str, message: str, mrd_number: str | None = None) -> HTTPException:
    return http_error(code, message, status.HTTP_500_INTERNAL_SERVER_ERROR, mrd_number)
