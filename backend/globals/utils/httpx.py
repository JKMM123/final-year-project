import httpx
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from globals.utils.logger import logger
from fastapi import Request


class HttpxClientManager:
    """
    Manager for a global httpx AsyncClient instance.
    """
    _client: Optional[httpx.AsyncClient] = None
    _base_url: Optional[str] = ""
    _headers: Dict[str, str] = {}
    _timeout: float = 100.0
    _limits: Optional[httpx.Limits] = None
    _verify_ssl: bool = False
    @classmethod
    def configure(
        cls,
        base_url: Optional[str] = "",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        keepalive_expiry: float = 60.0,
        verify_ssl: bool = False
    ) -> None:
        """
        Configure the global HTTPX client settings before initialization.
        
        Args:
            base_url: Optional base URL for all requests
            headers: Default headers to include in all requests
            timeout: Default timeout in seconds
            max_connections: Maximum number of connections
            max_keepalive_connections: Maximum number of idle connections to keep
            keepalive_expiry: Time in seconds to keep idle connections open
        """
        cls._base_url = base_url 
        cls._headers = headers or {}
        cls._timeout = timeout
        cls._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=keepalive_expiry
        )
        logger.info(f"HTTPX client configured with base_url={base_url}, timeout={timeout}s")
    

    @classmethod
    async def initialize(cls) -> None:
        """Initialize the global HTTPX client if not already initialized."""
        try:
            if cls._client is None:

                if cls._limits is None:
                    cls._limits = httpx.Limits(
                        max_connections=100,
                        max_keepalive_connections=20,
                        keepalive_expiry=100.0
                    )
                    logger.info("Default HTTPX client initialized successfully. ")


                cls._client = httpx.AsyncClient(
                    base_url=cls._base_url,
                    headers=cls._headers,
                    timeout=cls._timeout,
                    limits=cls._limits,
                    follow_redirects=True,
                    verify=cls._verify_ssl
                )
                logger.info("Global HTTPX client initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Error initializing HTTPX client: {e}")
            return False
    

    @classmethod
    async def close(cls) -> None:
        """Close the global HTTPX client if it exists."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
            logger.info("Global HTTPX client closed successfully. ")
    

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        """
        Get the global HTTPX client.
        
        Returns:
            httpx.AsyncClient: The global HTTPX client instance
            
        Raises:
            RuntimeError: If the client has not been initialized
        """
        if cls._client is None:
            raise RuntimeError(
                "HTTPX client not initialized. Call HttpxClientManager.initialize() first."
            )
        return cls._client
    



async def get_httpx_client(request: Request) -> httpx.AsyncClient:
    """
    FastAPI dependency for injecting the HTTPX client.
    """
    if not hasattr(request.app.state, "httpx_client_manager"):
        logger.warning("HTTP client not found in app state, initializing new instance")
        await HttpxClientManager.initialize()
        return HttpxClientManager.get_client()
        
    return request.app.state.httpx_client_manager.get_client()

