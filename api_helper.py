import asyncio

from fastapi import status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta

from core.browser import browser_pool

shutdown_event = asyncio.Event()


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


def signal_handler():
    """Handle exit signals"""

    async def _cleanup():
        # Set the shutdown event
        shutdown_event.set()
        # Wait for all tasks to complete and clean up resources
        await browser_pool.close()
        # Stop the event loop
        loop.stop()

    loop = asyncio.get_event_loop()
    loop.create_task(_cleanup())


def get_baidu_time_period(time_period: str) -> str:
    """
    Generate baidu time parameter based on time range
    Args:
        time_period (str): Time range, e.g. day (one day), week (one week), month (one month), year (one year)
    Returns:
        str: Baidu search time parameter
    """
    now = datetime.now()
    if time_period == "day":
        start_time = now - timedelta(days=1)
    elif time_period == "week":
        start_time = now - timedelta(weeks=1)
    elif time_period == "month":
        start_time = now - timedelta(days=30)
    elif time_period == "year":
        start_time = now - timedelta(days=365)
    else:
        return ""

    # Convert to Unix timestamp
    start_timestamp = int(start_time.timestamp())
    end_timestamp = int(now.timestamp())

    # Generate baidu search time parameter
    return f"stf%3D{start_timestamp}%2C{end_timestamp}%7Cstftype%3D1"
