from fastapi import Request, Response
from httpcore import request
from globals.responses.responses import internal_server_error_response
from globals.utils.logger import logger
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
from typing import Dict, Optional, Tuple
import time
from globals.utils.context import set_log_context, clear_log_context
from src.auth.routes.routes import ROUTE_CONFIG
from src.auth.services.jwtService import JWTService
from globals.utils.requestValidation import validate_request
from globals.exceptions.global_exceptions import (
    UnauthorizedError,
    ForbiddenError
)
from globals.responses.responses import (
    unauthorized_error_response,
    forbidden_error_response,
    too_many_requests_error_response
)
from src.auth.schemas.cookieSchema import CookieSchema
from src.auth.schemas.refreshSchema import RefreshSchema
from db.redis.connection import RedisManager


class GlobalInterceptor(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.route_config = ROUTE_CONFIG  # O(1) lookup

        # Pre-compile pattern matchers for parameterized routes
        self.pattern_cache = self._build_pattern_cache()
        
        # Initialize Redis for rate limiting
        self.redis = None
        
    def _build_pattern_cache(self):
        """Pre-build pattern matching cache for parameterized routes"""
        pattern_cache = {}
        
        for route_key in self.route_config.keys():
            method, path = route_key.split(":", 1)
            if "{" in path:  # Has parameters
                pattern_parts = path.strip("/").split("/")
                pattern_cache[route_key] = {
                    "method": method,
                    "parts": pattern_parts,
                    "param_count": len(pattern_parts)
                }
        
        return pattern_cache

    async def _get_redis_client(self):
        """Lazy initialize Redis client"""
        if self.redis is None:
            try:
                self.redis = await RedisManager.get_instance()
            except Exception as e:
                logger.error(f"Failed to initialize Redis: {e}")
                self.redis = None
        return self.redis


    def _get_route_config(self, request: Request) -> Optional[Dict]:
        """Fast O(1) lookup for route configuration"""
        method = request.method
        path = request.url.path
        
        # Try exact match first (fastest - O(1))
        exact_key = f"{method}:{path}"
        if exact_key in self.route_config:
            return self.route_config[exact_key]
        
        # Try pattern matching for parameterized routes
        path_parts = path.strip("/").split("/")
        path_part_count = len(path_parts)
        
        for route_key, pattern_info in self.pattern_cache.items():
            if (pattern_info["method"] == method and 
                pattern_info["param_count"] == path_part_count):
                
                # Check if pattern matches
                if self._fast_pattern_match(path_parts, pattern_info["parts"]):
                    return self.route_config[route_key]
        
        return None

    def _fast_pattern_match(self, actual_parts: list, pattern_parts: list) -> bool:
        """Fast pattern matching without regex"""
        for actual, pattern in zip(actual_parts, pattern_parts):
            if not (actual == pattern or pattern.startswith("{") and pattern.endswith("}")):
                return False
        return True


    def _get_rate_limit_key(self, request: Request) -> str:
        """Generate rate limit key based on IP address"""
        method = request.method
        path = request.url.path
        
        # For parameterized routes, use the pattern instead of actual values
        route_config = self._get_route_config(request)
        if route_config:
            # Try to find the original pattern from route_config keys
            for route_key in self.route_config.keys():
                stored_method, stored_path = route_key.split(":", 1)
                if method == stored_method:
                    if path == stored_path:
                        # Exact match
                        path = stored_path
                        break
                    elif "{" in stored_path and self._fast_pattern_match(
                        path.strip("/").split("/"), 
                        stored_path.strip("/").split("/")
                    ):
                        # Pattern match - use the pattern instead of actual path
                        path = stored_path
                        break
        
        return f"rl:{method}:{path}:ip:{request.client.host}"


    async def _check_rate_limits(self, key: str, limits: Dict[str, int]) -> Tuple[bool, Dict]:
        """Efficient rate limit checking with Redis pipeline"""
        redis_client = await self._get_redis_client()
        if not redis_client:
            # If Redis is down, allow request but log warning
            logger.warning("Redis unavailable, skipping rate limiting")
            return True, {"allowed": True, "remaining": 999}
        
        try:
            current_time = int(time.time())
            
            # Use single pipeline for all time windows
            pipe = redis_client.pipeline()
            
            windows = [
                ("minute", 60, limits["requests_per_minute"]),
                ("hour", 3600, limits["requests_per_hour"]),
                ("day", 86400, limits["requests_per_day"])
            ]
            
            # Add all operations to pipeline
            for window_name, seconds, limit in windows:
                window_key = f"{key}:{window_name}"
                pipe.zremrangebyscore(window_key, 0, current_time - seconds)
                pipe.zcard(window_key)
                pipe.zadd(window_key, {str(current_time): current_time})
                pipe.expire(window_key, seconds)
            
            # Execute all operations at once
            results = await pipe.execute()
            
            # Check results (every 4th result is the count)
            for i, (window_name, seconds, limit) in enumerate(windows):
                count_idx = i * 4 + 1  # zcard result index
                current_count = results[count_idx]
                
                if current_count > limit:  # > because we already added the current request
                    return False, {
                        "allowed": False,
                        "limit": limit,
                        "current": current_count,
                        "window": window_name,
                        "retry_after": seconds
                    }
            
            # Calculate remaining (most restrictive)
            remaining = min(
                limit - results[i * 4 + 1] 
                for i, (_, _, limit) in enumerate(windows)
            )
            
            return True, {
                "allowed": True,
                "remaining": max(0, remaining)
            }
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # If rate limiting fails, allow the request
            return True, {"allowed": True, "remaining": 999}

    async def dispatch(self, request: Request, call_next):
        try:
            trace_id = request.headers.get("X-Trace-Id", str(uuid4()))
            request_path = request.url.path
            request_method = request.method

            await set_log_context(
                reference_id=trace_id,
                path=request_path,
                method=request_method,
                host_from=request.client.host
            )
            
            logger.info("Entered billing-system")
            
            # **STEP 1: Handle refresh token endpoint**
            if "/refresh" in request_path:
                logger.info("Refresh endpoint accessed")
                valid, validated_data = await validate_request(
                    request=request, 
                    cookie_model=RefreshSchema
                ) 
                if not valid:
                    logger.error(f"Validation error: {validated_data}")
                    raise UnauthorizedError(message="Invalid refresh token cookies")
                
                decoded_token = JWTService.verify_refresh_token(
                    token=request.cookies.get("refresh_token")
                )
                decoded_token.update({
                    "refresh_token": validated_data.get('cookies').get('refresh_token')
                })
                request.state.user = decoded_token
                
                response = await call_next(request)
                await clear_log_context()
                return response
            
            # **STEP 2: Get route configuration (O(1) lookup)**
            route_config = self._get_route_config(request)

            if not route_config:
                logger.warning(f"Route not found: {request_method} {request_path}")
                await clear_log_context()
                return await call_next(request)  # Let FastAPI handle 404
            

            # **STEP 3: Check rate limits FIRST**
            if "rate_limit" in route_config:
                rate_limit_key = self._get_rate_limit_key(request)
                
                is_allowed, rate_info = await self._check_rate_limits(
                    rate_limit_key, 
                    route_config["rate_limit"]
                )
                
                if not is_allowed:
                    logger.warning(f"Rate limit exceeded for {rate_limit_key}")
                    await clear_log_context()
                    return too_many_requests_error_response(
                        message=f"Rate limit exceeded: {rate_info['limit']} requests per {rate_info['window']}. Try again in {rate_info['retry_after']} seconds."
                    )
            
            # **STEP 4: Check if route is public**
            is_public = route_config.get("public", False)
            
            if is_public:
                logger.info(f"Public route accessed: {request_path}")
                response = await call_next(request)
                await clear_log_context()
                return response
            
            
            # **STEP 5: Protected route - validate JWT and check roles**
            logger.info(f"Protected route accessed: {request_path}")
            
            # Validate cookies + JWT
            valid, validated = await validate_request(
                request=request, 
                cookie_model=CookieSchema
            )
            if not valid:
                raise UnauthorizedError("Invalid access token cookies")
            
            # Verify JWT token
            decoded = JWTService.verify_access_token(validated['cookies']['access_token'])
            request.state.user = decoded
            
            # Check role permissions
            required_roles = route_config.get("roles", set())
            user_role = decoded.get("role")
            
            if user_role not in required_roles:
                raise ForbiddenError("You do not have permission to access this resource.")
            
            logger.info(f"User {decoded.get('user_id')} with role '{user_role}' accessing {request_path}")
            
            # Process the request
            response: Response = await call_next(request)
            await clear_log_context()
            return response
        
        except UnauthorizedError as e:
            await clear_log_context()
            return unauthorized_error_response(message=e.message)
        
        except ForbiddenError as e:
            await clear_log_context()
            return forbidden_error_response(message=e.message)

        except Exception as e:
            logger.error(f"Error in GlobalInterceptor: {str(e)}")
            await clear_log_context()
            return internal_server_error_response(
                message="An unexpected error occurred."
            )