from fastapi import FastAPI
from globals.utils.logger import logger

from globals.utils.httpx import HttpxClientManager

from db.postgres.connection import PostgresClient
from db.postgres.entities import create_all_entities

from src.auth.services.authService import AuthService
from src.auth.queries.authQueries import AuthQueries

from src.users.queries.usersQueries import UsersQueries
from src.users.queries.seedSystemUser import seed_system_user_in_pg
from src.users.services.usersService import UsersService

from src.rates.queries.ratesQueries import RatesQueries
from src.rates.services.ratesService import RatesService

from src.packages.queries.packagesQueries import PackagesQueries
from src.packages.services.packagesService import PackagesService

from src.meters.queries.metersQueries import MetersQueries
from src.meters.services.metersService import MetersService
from src.meters.services.meterFileService import MeterFileService

from db.gcs.gcsService import GCSManager

from src.readings.services.readingsService import ReadingsService
from src.readings.services.scanningServiceV2 import ScanningService
from src.readings.queries.readingsQueries import ReadingsQueries

from src.bills.queries.billsQueries import BillsQueries
from src.bills.services.billsService import BillsService

from src.areas.queries.areasQueries import AreasQueries
from src.areas.services.areasService import AreasService

from src.dashboard.queries.dashboardQueries import DashboardQueries
from src.dashboard.services.dashboardService import DashboardService

from src.messages.services.messagesService import MessagesService
from src.messages.services.whatsappSessionService import WhatsAppSessionService
from src.messages.services.whatsappMessagesService import WhatsappMessagesService

from db.redis.connection import RedisManager

from src.fixes.queries.fixesQueries import FixesQueries
from src.fixes.services.fixesService import FixesService

from src.templates.services.templatesService import TemplatesService

from db.postgres.migration import apply_migrations_with_retry


from src.payments.services.paymentsService import PaymentsService

class AppInitializer:
    _status = {
        "httpx_client_manager": False,
        "postgres": False,
        "auth_queries": False,
        "auth_service": False,
        "users_queries": False,
        "users_service": False,
        "seed_system_user": False,
        "seed_rates":False,
        "rates_queries": False,
        "rates_service": False,
        "packages_queries": False,
        "packages_service": False,
        "meters_queries": False,
        "meters_service": False,
        "meter_file_service": False,
        "gcs_manager": False,
        "bucket_created": False,
        "readings_queries": False,
        "scanning_service": False,
        "readings_service": False,
        "bills_queries": False,
        "bills_service": False,
        "redis_manager": False,
        "fixes_queries": False,
        "fixes_service": False,
        "templates_service": False,
        "whatsapp_session_service": False,
        "messages_service": False,
        "whatsapp_messages_service": False,
        "migration": False,
        "payments_service": False

    }

    @classmethod
    async def initialize(cls, app: FastAPI):
        try:
            # Initialize HTTPX Client Manager
            logger.info("Initializing HTTPX client manager...")
            success = await HttpxClientManager.initialize() 
            if success:
                cls._status["httpx_client_manager"] = True
                logger.info("HTTPX client manager initialized successfully")
            else:
                logger.error("Failed to initialize HTTPX client manager")
                return False

            # Run Migration
            logger.info("Applying database migrations...")
            try:
                await apply_migrations_with_retry()
                cls._status["migration"] = True
                logger.info("Database migrations applied successfully")

            except Exception as e:
                logger.error(f"Error applying database migrations: {str(e)}")
                return False

            # Initialize PostgreSQL
            logger.info("Initializing PostgreSQL connection...")
            success = await PostgresClient.init_async_engine()
            if success:
                cls._status["postgres"] = True
                logger.info("PostgreSQL connection established")
                
                # # Create database entities
                # db_initialized = await create_all_entities(PostgresClient)
                # if not db_initialized:
                #     logger.warning("Database initialization failed, some features may not work")
            else:
                logger.error("Failed to initialize PostgreSQL client")
                return False
            
            # Initialize Redis
            logger.info("Initializing Redis connection...")
            try:
                redis_manager = await RedisManager.get_instance()
                cls._status["redis_manager"] = True
            except Exception as e:
                logger.error(f"Error initializing Redis connection: {e}")
                return False
            
            # Initialize GCS Manager
            logger.info("Initializing GCS Manager...")
            try:
                gcs_manager = GCSManager()
                cls._status["gcs_manager"] = True
            except Exception as e:
                logger.error(f"Error initializing GCS Manager: {str(e)}")
                return False
            
            # Create GCS bucket
            logger.info("Creating GCS bucket...")
            try:
                bucket_name = "electricity-billing-system-bucket-automation-f46ca"
                location = "europe-west1"
                bucket = gcs_manager.create_bucket(bucket_name, location)
                cls._status["bucket_created"] = True
            except Exception as e:
                logger.error(f"Error creating GCS bucket: {str(e)}")
                return False

            # Initialize Auth Queries
            logger.info("Initializing Auth Queries...")
            try:
                auth_queries = AuthQueries()
                cls._status["auth_queries"] = True
            
            except Exception as e:
                logger.error(f"Error initializing Auth Queries: {str(e)}")
                return False
            
            try:
                await seed_system_user_in_pg()
                cls._status["seed_system_user"] = True
            except Exception as e:
                logger.error(f"Error seeding system user: {str(e)}")
                return False

            # Initialize Auth Service
            logger.info("Initializing Auth Service...")
            try:
                auth_service = AuthService(
                    auth_queries=auth_queries
                    )
                cls._status["auth_service"] = True
                app.state.auth_service = auth_service
            except Exception as e:
                logger.error(f"Error initializing Auth Service: {str(e)}")
                return False

            # Initialize Users Queries
            logger.info("Initializing Users Queries...")
            try:
                users_queries = UsersQueries()
                cls._status["users_queries"] = True
                app.state.users_queries = users_queries
            except Exception as e:
                logger.error(f"Error initializing Users Queries: {str(e)}")
                return False

            # Initialize Users Service
            logger.info("Initializing Users Service...")
            try:
                users_service = UsersService(
                    users_queries=users_queries
                )
                cls._status["users_service"] = True
                app.state.users_service = users_service

            except Exception as e:
                logger.error(f"Error initializing Users Service: {str(e)}")
                return False
            
            
            # Initialize Rates Queries
            logger.info("Initializing Rates Queries...")
            try:
                rates_queries = RatesQueries()
                cls._status["rates_queries"] = True
                app.state.rates_queries = rates_queries

            except Exception as e:
                logger.error(f"Error initializing Rates Queries: {str(e)}")
                return False
            
            # Initialize Rates Service
            logger.info("Initializing Rates Service...")
            try:
                rates_service = RatesService(
                    rates_queries=rates_queries
                )
                cls._status["rates_service"] = True
                app.state.rates_service = rates_service
            
            except Exception as e:
                logger.error(f"Error initializing Rates Service: {str(e)}")
                return False
            
            # Initialize Packages Queries
            logger.info("Initializing Packages Queries...")
            try:
                packages_queries = PackagesQueries()
                cls._status["packages_queries"] = True
                app.state.packages_queries = packages_queries

            except Exception as e:
                logger.error(f"Error initializing Packages Queries: {str(e)}")
                return False

            # Initialize Packages Service
            logger.info("Initializing Packages Service...")
            try:
                packages_service = PackagesService(
                    packages_queries=packages_queries
                )
                cls._status["packages_service"] = True
                app.state.packages_service = packages_service

            except Exception as e:
                logger.error(f"Error initializing Packages Service: {str(e)}")
                return False
            
            # Initialize Areas Queries
            logger.info("Initializing Areas Queries...")
            try:
                areas_queries = AreasQueries()
                cls._status["areas_queries"] = True
                app.state.areas_queries = areas_queries

            except Exception as e:
                logger.error(f"Error initializing Areas Queries: {str(e)}")
                return False
            
            # Initialize Areas Service
            logger.info("Initializing Areas Service...")
            try:
                areas_service = AreasService(
                    areas_queries=areas_queries
                )
                cls._status["areas_service"] = True
                app.state.areas_service = areas_service

            except Exception as e:
                logger.error(f"Error initializing Areas Service: {str(e)}")
                return False

            # Initialize Meters Queries
            logger.info("Initializing Meters Queries...")
            try:
                meters_queries = MetersQueries(
                    gcs_manager=gcs_manager
                )
                cls._status["meters_queries"] = True
                app.state.meters_queries = meters_queries

            except Exception as e:
                logger.error(f"Error initializing Meters Queries: {str(e)}")
                return False

            # Initialize Meters Service
            logger.info("Initializing Meters Service...")
            try:
                meters_service = MetersService(
                    meters_queries=meters_queries
                )
                cls._status["meters_service"] = True
                app.state.meters_service = meters_service

            except Exception as e:
                logger.error(f"Error initializing Meters Service: {str(e)}")
                return False
            
            # Initialize Meter File Service
            logger.info("Initializing Meter File Service...")
            try:
                meter_file_service = MeterFileService(
                    meters_queries=meters_queries
                )
                cls._status["meter_file_service"] = True
                app.state.meter_file_service = meter_file_service
            except Exception as e:
                logger.error(f"Error initializing Meter File Service: {str(e)}")
                return False
            
            
            # Initialize Readings Queries
            logger.info("Initializing Readings Queries...")
            try:
                readings_queries = ReadingsQueries(
                    gcs_manager=gcs_manager
                )
                cls._status["readings_queries"] = True
                app.state.readings_queries = readings_queries

            except Exception as e:
                logger.error(f"Error initializing Readings Queries: {str(e)}")
                return False

            # Initialize Readings Service
            logger.info("Initializing Readings Service...")
            try:
                readings_service = ReadingsService(
                    readings_queries=readings_queries
                )
                cls._status["readings_service"] = True
                app.state.readings_service = readings_service

            except Exception as e:
                logger.error(f"Error initializing Readings Service: {str(e)}")
                return False
            
            # Initialize Scanning Service
            logger.info("Initializing Scanning Service...")
            try:
                scanning_service = ScanningService(
                    readings_queries=readings_queries
                )
                cls._status["scanning_service"] = True
                app.state.scanning_service = scanning_service

            except Exception as e:
                logger.error(f"Error initializing Scanning Service: {str(e)}")
                return False

            # Initialize Bills Queries
            logger.info("Initializing Bills Queries...")
            try:
                bills_queries = BillsQueries()
                cls._status["bills_queries"] = True
                app.state.bills_queries = bills_queries

            except Exception as e:
                logger.error(f"Error initializing Bills Queries: {str(e)}")
                return False

            # Initialize Bills Service
            logger.info("Initializing Bills Service...")
            try:
                bills_service = BillsService(
                    bills_queries=bills_queries
                )
                cls._status["bills_service"] = True
                app.state.bills_service = bills_service

            except Exception as e:
                logger.error(f"Error initializing Bills Service: {str(e)}")
                return False

            # Initialize Fixes Queries
            logger.info("Initializing Fixes Queries...")
            try:
                fixes_queries = FixesQueries()
                cls._status["fixes_queries"] = True
                app.state.fixes_queries = fixes_queries

            except Exception as e:
                logger.error(f"Error initializing Fixes Queries: {str(e)}")
                return False

            # Initialize Fixes Service
            logger.info("Initializing Fixes Service...")
            try:
                fixes_service = FixesService(
                    fixes_queries=fixes_queries
                )
                cls._status["fixes_service"] = True
                app.state.fixes_service = fixes_service

            except Exception as e:
                logger.error(f"Error initializing Fixes Service: {str(e)}")
                return False

            # Initialize Templates Service
            logger.info("Initializing Templates Service...")
            try:
                templates_service = TemplatesService()
                cls._status["templates_service"] = True
                app.state.templates_service = templates_service

            except Exception as e:
                logger.error(f"Error initializing Templates Service: {str(e)}")
                return False

            # Initialize Dashboard Queries
            logger.info("Initializing Dashboard Queries...")
            try:
                dashboard_queries = DashboardQueries()
                cls._status["dashboard_queries"] = True
                app.state.dashboard_queries = dashboard_queries

            except Exception as e:
                logger.error(f"Error initializing Dashboard Queries: {str(e)}")
                return False

            # Initialize Dashboard Service
            logger.info("Initializing Dashboard Service...")
            try:
                dashboard_service = DashboardService(
                    dashboard_queries=dashboard_queries
                )
                cls._status["dashboard_service"] = True
                app.state.dashboard_service = dashboard_service

            except Exception as e:
                logger.error(f"Error initializing Dashboard Service: {str(e)}")
                return False

            # Initialize Messages Service
            logger.info("Initializing Messages Service...")
            try:
                messages_service = MessagesService()
                cls._status["messages_service"] = True
                app.state.messages_service = messages_service

            except Exception as e:
                logger.error(f"Error initializing Dashboard Service: {str(e)}")
                return False

            # Initialize WhatsApp Session Service
            logger.info("Initializing WhatsApp Session Service...")
            try:
                whatsapp_session_service = WhatsAppSessionService()
                cls._status["whatsapp_session_service"] = True
                app.state.whatsapp_session_service = whatsapp_session_service

            except Exception as e:
                logger.error(f"Error initializing WhatsApp Session Service: {str(e)}")
                return False

            # Initialize WhatsApp Messages Service
            logger.info("Initializing WhatsApp Messages Service...")
            try:
                whatsapp_messages_service = WhatsappMessagesService()
                cls._status["whatsapp_messages_service"] = True
                app.state.whatsapp_messages_service = whatsapp_messages_service

            except Exception as e:
                logger.error(f"Error initializing WhatsApp Messages Service: {str(e)}")
                return False
            
            # Initialize Payments Service
            logger.info("Initializing Payments Service...")
            try:
                payments_service = PaymentsService()
                cls._status["payments_service"] = True
                app.state.payments_service = payments_service

            except Exception as e:
                logger.error(f"Error initializing Payments Service: {str(e)}")
                return False

            logger.info("All services initialized successfully!")
            return True
        
        except Exception as e:
            logger.error(f"Critical error during initialization: {e}")
            await cls.cleanup()
            return False


    @classmethod
    async def cleanup(cls):
        try:
            if cls._status.get("postgres"):
                await PostgresClient.close_async_engine()
                logger.info("PostgreSQL connection closed")

            if cls._status.get("redis_manager"):
                await RedisManager.close()
                logger.info("Redis connection closed")

            if cls._status.get("httpx_client_manager"):
                await HttpxClientManager.close()
                logger.info("HTTPX client manager closed")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


    @classmethod
    def get_status(cls) -> dict:
        """Get initialization status of all services."""
        return cls._status.copy()


    @classmethod
    def is_healthy(cls) -> bool:
        """Check if all critical services are initialized."""
        critical_services = [
            "postgres",
            "redis_manager",
            "httpx_client_manager"
        ]
        return all(cls._status.get(service, False) for service in critical_services)
