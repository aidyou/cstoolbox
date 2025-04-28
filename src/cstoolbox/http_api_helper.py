from fastapi import status
from fastapi.responses import JSONResponse


def fail(
    message: str,
    detail: str | None = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    add_error_status_code: bool = False,
) -> JSONResponse:
    """
    Return a JSON response with a failure message and status code

    Args:
        message (str): Failure message.
        detail (str, optional): Additional details. Defaults to None.
        status_code (int, optional): HTTP status code. Defaults to 500.

    Returns:
        JSONResponse: JSON response with failure message and status code
    """
    content = {"code": status_code, "data": None, "message": message}
    if detail:
        content["detail"] = detail
    return JSONResponse(
        status_code=status_code if add_error_status_code else status.HTTP_200_OK,
        content=content,
    )


def success(data: dict | str = None, message: str = "") -> JSONResponse:
    """
    Return a JSON response with a success message and data

    Args:
        data (dict | str, optional): Data to return. Defaults to None.
        message (str, optional): Success message. Defaults to "".

    Returns:
        JSONResponse: JSON response with success message and data
    """
    content = {"code": status.HTTP_200_OK, "data": data}
    if message:
        content["message"] = message
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=content,
    )
