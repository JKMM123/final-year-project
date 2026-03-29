import uvicorn
from fastapi import FastAPI
from fastapi import Request
from contextlib import asynccontextmanager
from src.app_state.init import AppInitializer
from fastapi.middleware.cors import CORSMiddleware
from globals.utils.logger import logger
from globals.middlewares.GlobalInterceptor import GlobalInterceptor
from globals.config.config import FRONT_END_URL

# routers
from src.app_state.router import health_router
from src.rates.routers.ratesRouter import rates_router
from src.auth.routers.authRouter import auth_router
from src.users.routers.usersRouter import users_router
from src.packages.routers.packagesRouter import packages_router
from src.meters.routers.metersRouter import meters_router
from src.readings.routers.readingsRouter import readings_router
from src.bills.routers.billsRouter import bills_router
from src.areas.routers.areasRouter import areas_router
from src.dashboard.routers.dashboardRouter import dashboard_router
from src.fixes.routers.fixesRouter import fixes_router
from src.templates.routers.templatesRouter import templates_router
from src.messages.routers.messagesRouter import messages_router
from src.celery.router import celery_router
from src.messages.routers.whatsappSessionRouter import whatsapp_session_router
from src.payments.routers.paymentsRouter import payments_router

# exceptions
from globals.exceptions.register import register_global_exceptions
from src.users.exceptions.register import register_users_exceptions
from src.auth.exceptions.register import register_auth_exceptions
from src.packages.exceptions.register import register_packages_exceptions
from src.meters.exceptions.register import register_meters_exceptions
from src.readings.exceptions.register import register_readings_exceptions
from src.bills.exceptions.register import register_bills_exceptions
from src.areas.exceptions.register import register_areas_exceptions
from src.fixes.exceptions.register import register_fixes_exceptions
from src.templates.exceptions.register import register_templates_exceptions
from src.messages.exceptions.register import register_messages_exceptions
from src.payments.exceptions.register import register_payments_exceptions
from src.rates.exceptions.register import register_rates_exceptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await AppInitializer.initialize(app)

        yield
    finally:
        await AppInitializer.cleanup()


app = FastAPI(
    lifespan=lifespan,
    title="Billing System",
    description="A billing system",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/swagger-ui/index.html",
    openapi_tags=[{"name": "Billing System", "description": "A billing system"}],
    root_path="/billing-system",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONT_END_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GlobalInterceptor)


# Register exceptions
register_global_exceptions(app)
register_auth_exceptions(app)
register_users_exceptions(app)
register_packages_exceptions(app)
register_meters_exceptions(app)
register_readings_exceptions(app)
register_bills_exceptions(app)
register_areas_exceptions(app)
register_fixes_exceptions(app)
register_templates_exceptions(app)
register_messages_exceptions(app)
register_payments_exceptions(app)
register_rates_exceptions(app)


# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(rates_router)
app.include_router(packages_router)
app.include_router(meters_router)
app.include_router(readings_router)
app.include_router(bills_router)
app.include_router(areas_router)
app.include_router(dashboard_router)
app.include_router(fixes_router)
app.include_router(templates_router)
app.include_router(messages_router)
app.include_router(celery_router)
app.include_router(whatsapp_session_router)
app.include_router(payments_router)


if __name__ == "__main__":
    try:
        import uvicorn

        config = uvicorn.Config(
            "main:app",
            host="0.0.0.0",
            port=8080,
            http="httptools",
            loop="asyncio",
            log_level="debug",
            access_log=True,
            use_colors=True,
            # workers=1
            # ssl_certfile="secrets/cert.pem",
            # ssl_keyfile="secrets/key.pem",
        )

        server = uvicorn.Server(config)
        server.run()

    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise e
