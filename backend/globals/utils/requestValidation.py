
from fastapi import Request
from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional, Type, Any, Tuple, Union


async def validate_request(
    request: Request,
    body_model: Optional[Type[BaseModel]] = None,
    query_model: Optional[Type[BaseModel]] = None,
    path_model: Optional[Type[BaseModel]] = None,
    header_model: Optional[Type[BaseModel]] = None,
    cookie_model: Optional[Type[BaseModel]] = None
) -> Tuple[bool, Union[Dict[str, Any], List[Dict[str, str]]]]:
    """
    Validates all parts of a request against provided Pydantic models.
    
    Args:
        request: The FastAPI request object
        body_model: Pydantic model for request body
        query_model: Pydantic model for query parameters
        path_model: Pydantic model for path parameters
        header_model: Pydantic model for headers
        
    Returns:
        Tuple containing:
        - Boolean indicating if validation passed
        - If validation passed: Combined dict of validated data
        - If validation failed: List of validation errors
    """
    errors = []
    validated_data = {} 
    
    # Validate request body
    if body_model:
        try:
            body_data = await request.json() if await request.body() else {}
            validated_body = body_model(**body_data)
            validated_data["body"] = validated_body.model_dump()
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append({
                    "field": f"{field.replace('_', ' ')}",
                    "message": error["msg"]
                })
        except Exception as e:
            errors.append({
                "field": "body",
                "message": f"{str(e)}"
            })
    
    # Validate query parameters
    if query_model:
        try:
            validated_query = query_model(**dict(request.query_params))
            validated_data["query"] = validated_query.model_dump()
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append({
                    "field": f"{field.replace('_',' ' )}",
                    "message": error["msg"]
                })
    
    # Validate path parameters
    if path_model:
        try:
            validated_path = path_model(**dict(request.path_params))
            validated_data["path"] = validated_path.model_dump()
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append({
                    "field": f"{field.replace('_',' ')}",
                    "message": error["msg"]
                })
    
    # Validate headers
    if header_model:
        try:
            headers = {k.lower(): v for k, v in request.headers.items()}
            validated_headers = header_model(**headers)
            validated_data["headers"] = validated_headers.model_dump()
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append({
                    "field": f"{field.replace('_',' ')}",
                    "message": error["msg"]
                })

    if cookie_model:
        try:
            cookies = {k: v for k, v in request.cookies.items()}
            validated_cookies = cookie_model(**cookies)
            validated_data["cookies"] = validated_cookies.model_dump()
        except ValidationError as e:
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                errors.append({
                    "field": f"{field.replace('_',' ')}",
                    "message": error["msg"]
                })
    
    # Return validation result
    if errors:
        return False, errors
    
    return True, validated_data
