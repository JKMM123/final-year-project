from fastapi import status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from globals.responses.globalResposneSchemas import RequestErrors, RequestResponse
from globals.config.config import FRONT_END_URL


def get_utc_timestamp():
    return datetime.now(timezone.utc).isoformat()
 

def unauthorized_error_response(message:str = "Unauthorized"):
    error_response = RequestErrors(
        message=message,
        error="Unauthorized",
        fieldErrors=[],
        status=status.HTTP_401_UNAUTHORIZED,
        timeStamp=get_utc_timestamp()
    )

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=error_response.model_dump(),
        headers={
            "Access-Control-Allow-Origin": FRONT_END_URL,
            "Access-Control-Allow-Credentials": "true",
        },
)



def forbidden_error_response(message: str = "Forbidden", error: str = "Forbidden"):
    error_response = RequestErrors(
        message=message,
        error=error,
        fieldErrors=[],
        status=status.HTTP_403_FORBIDDEN,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response.model_dump(),
        headers={
            "Access-Control-Allow-Origin": FRONT_END_URL,
            "Access-Control-Allow-Credentials": "true",
        }
    )


def validation_error_response(errors, message: str = "Validation Error"):
    error_response = RequestErrors(
        message=message,
        error="Validation Error",
        fieldErrors=errors,
        status=status.HTTP_400_BAD_REQUEST,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )
 
 
def bad_request_error_response(error="Bad Request", message: str = "Bad Request"):
    error_response = RequestErrors(
        message=message,
        error=error,
        fieldErrors=[],
        status=status.HTTP_400_BAD_REQUEST,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response.model_dump()
    )
 
 
def internal_server_error_response(message, fieldErrors=[]):
    error_response = RequestErrors(
        message=message,
        error="Internal Server Error",
        fieldErrors=fieldErrors,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )
 
 
def not_found_error_response(error="Not Found", message: str = "Not Found"):
    error_response = RequestErrors(
        message=message,
        error=error,
        fieldErrors=[],
        status=status.HTTP_404_NOT_FOUND,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=error_response.model_dump()
    )
 
 
def success_response(message: str, data):
    response = RequestResponse(
        message=message,
        data=data,
        status=status.HTTP_200_OK,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump()
    )

def time_out_error_response(error="Timeout", message: str = "Request Timeout"):
    error_response = RequestErrors(
        message=message,
        error=error,
        fieldErrors=[],
        status=status.HTTP_408_REQUEST_TIMEOUT,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content=error_response.model_dump(),
        headers={
            "Access-Control-Allow-Origin": FRONT_END_URL,
            "Access-Control-Allow-Credentials": "true",
        }
    )

def too_many_requests_error_response(message: str = "Too Many Requests"):
    error_response = RequestErrors(
        message=message,
        error="Too Many Requests",
        fieldErrors=[],
        status=status.HTTP_429_TOO_MANY_REQUESTS,
        timeStamp=get_utc_timestamp()
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.model_dump(),
        headers={
            "Access-Control-Allow-Origin": FRONT_END_URL,
            "Access-Control-Allow-Credentials": "true",
        }
    )