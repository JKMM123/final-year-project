from enum import Enum
from starlette.routing import Route
from globals.utils.logger import logger

from src.app_state.router import health_check

from src.auth.routers.authRouter import(
    login,
    logout,
    get_me,
    validate_token,
    reset_password,
    send_otp,
    verify_otp
)

from src.users.routers.usersRouter import (
    get_user,
    create_user,
    update_user,
    delete_user,
    search_users,
)

from src.rates.routers.ratesRouter import (
    update_rates,
    create_rates,
    delete_rates,
    get_rates_by_date,
    search_rates,
    get_all_rates_by_year
)

from src.packages.routers.packagesRouter import (
    get_package,
    create_package,
    update_package,
    delete_package,
    search_packages,
)

from src.meters.routers.metersRouter import (
    get_meter,
    create_meter,
    update_meter,
    delete_meter,
    search_meters,
    get_meter_qr_code,
    get_meter_qr_codes,
    upload_meters,
    delete_meters
)

from src.readings.routers.readingsRouter import (
    create_reading,
    get_reading,
    update_reading,
    delete_reading,
    search_readings,
    get_readings_summary,
    scan_reading,
    verify_all_readings
)

from src.bills.routers.billsRouter import (
    get_bill,
    # update_bill,
    delete_bill,
    search_bills,
    generate_bills,
    download_bills
    )

from src.areas.routers.areasRouter import (
    create_area,
    search_areas,
    delete_area,
    update_area
)


from src.dashboard.routers.dashboardRouter import (
    get_dashboard_summary
)


from src.fixes.routers.fixesRouter import (
    create_fix,
    search_fixes,
    update_fix,
    delete_fixes,
    get_fix
)

from src.templates.routers.templatesRouter import (
    create_template,
    get_template,
    update_template,
    delete_template,
    search_templates
)

from src.messages.routers.messagesRouter import (
    send_messages,
)

from src.celery.router import (
    get_task_status
)

from src.messages.routers.whatsappSessionRouter import (
    create_session,
    delete_session,
    get_session_status,
    connect_session,
    handle_webhook_events,
    get_webhook_events
)

from src.payments.routers.paymentsRouter import (
    create_payment,
    get_payment_by_id,
    update_payment,
    delete_payment,
    get_all_payments_by_bill_id,
    mark_all_bills_as_paid
)


def create_routes_config():
    routes = [
        # Health check route
        {
            "path": "/billing-system/health",
            "method": "GET",
            "endpoint": health_check,
            "public": True,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 50, "requests_per_hour": 2000, "requests_per_day": 50000}
        },
        # Auth routes
        {
            "path": "/billing-system/api/v1/auth/login",
            "method": "POST",
            "endpoint": login,
            "public": True,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 5, "requests_per_hour": 20, "requests_per_day": 50}
        },
        {
            "path": "/billing-system/api/v1/auth/logout",
            "method": "POST",
            "endpoint": logout,
            "public": False,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 5, "requests_per_hour": 20, "requests_per_day": 50}
        },
        {
            "path": "/billing-system/api/v1/auth/me",
            "method": "GET",
            "public": False,
            "endpoint": get_me,
            "roles": {"system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/auth/validate-token",
            "method": "GET",
            "public": False,
            "endpoint": validate_token,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/auth/reset-password",
            "method": "POST",
            "public": True,
            "endpoint": reset_password,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 20, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/auth/send-otp",
            "method": "POST",
            "public": True,
            "endpoint": send_otp,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 3, "requests_per_hour": 10, "requests_per_day": 100}
        },
        {
            "path": "/billing-system/api/v1/auth/verify-otp",
            "method": "POST",
            "public": True,
            "endpoint": verify_otp,
            "roles": {"admin", "system", "user"},
            "rate_limit": {"requests_per_minute": 5, "requests_per_hour": 20, "requests_per_day": 50}
        },
        # User routes
        {            
            "path": "/billing-system/api/v1/users/search",
            "method": "GET",
            "public": False,
            "endpoint": search_users,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path":"/billing-system/api/v1/users/create",
            "method": "POST",
            "public": False,
            "endpoint": create_user,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/users/{user_id}",
            "method": "GET",
            "endpoint": get_user,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/users/{user_id}",
            "method": "PUT",
            "endpoint": update_user,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/users/{user_id}",
            "method": "DELETE",
            "endpoint": delete_user,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Area routes
        {
            "path": "/billing-system/api/v1/areas/create",
            "method": "POST",
            "endpoint": create_area,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/areas/search",
            "method": "GET",
            "endpoint": search_areas,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/areas/{area_id}",
            "method": "DELETE",
            "endpoint": delete_area,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/areas/{area_id}",
            "method": "PUT",
            "endpoint": update_area,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Rates routes
        {
            "path": "/billing-system/api/v1/rates/create",
            "method": "POST",
            "endpoint": create_rates,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 60, "requests_per_hour": 3600, "requests_per_day": 50000}
        },
        {
            "path": "/billing-system/api/v1/rates/search",
            "method": "GET",
            "endpoint": search_rates,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 60, "requests_per_hour": 3600, "requests_per_day": 50000}
        },
        {
            "path": "/billing-system/api/v1/rates/all/{year}",
            "method": "GET",
            "endpoint": get_all_rates_by_year,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 60, "requests_per_hour": 3600, "requests_per_day": 50000}
        },
        {
            "path": "/billing-system/api/v1/rates/{rate_id}",
            "method": "PUT",
            "endpoint": update_rates,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 60, "requests_per_hour": 3600, "requests_per_day": 50000}
        },
        {
            "path": "/billing-system/api/v1/rates/{effective_date}",
            "method": "GET",
            "endpoint": get_rates_by_date,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 60, "requests_per_hour": 3600, "requests_per_day": 50000}
        },
        {
            "path": "/billing-system/api/v1/rates/{rate_id}",
            "method": "DELETE",
            "endpoint": delete_rates,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 60, "requests_per_hour": 3600, "requests_per_day": 50000}
        },
        # Package routes
        {
            "path": "/billing-system/api/v1/packages/search",
            "method": "GET",
            "endpoint": search_packages,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/packages/create",
            "method": "POST",
            "endpoint": create_package,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/packages/{package_id}",
            "method": "GET",
            "endpoint": get_package,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/packages/{package_id}",
            "method": "PUT",
            "endpoint": update_package,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/packages/{package_id}",
            "method": "DELETE",
            "endpoint": delete_package,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Meter routes
        {
            "path": "/billing-system/api/v1/meters/search",
            "method": "POST",
            "endpoint": search_meters,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/meters/create",
            "method": "POST",
            "endpoint": create_meter,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/meters/qr-codes",
            "method": "GET",
            "endpoint": get_meter_qr_codes,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/meters/upload",
            "method": "POST",
            "endpoint": upload_meters,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/meters/delete",
            "method": "DELETE",
            "endpoint": delete_meters,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/meters/{meter_id}",
            "method": "GET",
            "endpoint": get_meter,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/meters/{meter_id}",
            "method": "PUT",
            "endpoint": update_meter,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            'path': '/billing-system/api/v1/meters/{meter_id}',
            'method': 'DELETE',
            'endpoint': delete_meter,
            "public": False,
            'roles': {'admin', 'system'},
            'rate_limit': {'requests_per_minute': 10, 'requests_per_hour': 100, 'requests_per_day': 1000}
        },
        {
            "path":"/billing-system/api/v1/meters/{meter_id}/qr-code",
            "method": "GET",
            "endpoint": get_meter_qr_code,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Readings routes
        {
            "path": "/billing-system/api/v1/readings/search",
            "method": "POST",
            "endpoint": search_readings,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/readings/create",
            "method": "POST",
            "endpoint": create_reading,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path":"/billing-system/api/v1/readings/summary",
            "method": "GET",
            "endpoint": get_readings_summary,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/readings/{reading_id}",
            "method": "GET",
            "endpoint": get_reading,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/readings/{reading_id}",
            "method": "PUT",
            "endpoint": update_reading,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/readings/{reading_id}",
            "method": "DELETE",
            "endpoint": delete_reading,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path":"/billing-system/api/v1/readings/{meter_id}/scan",
            "method": "POST",
            "endpoint": scan_reading,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 10000, "requests_per_day": 100000}
        },
        {
            "path":"/billing-system/api/v1/readings/verify-all",
            "method": "POST",
            "endpoint": verify_all_readings,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 10000, "requests_per_day": 100000}
        },
        # Bills routes
        {
            "path": "/billing-system/api/v1/bills/search",
            "method": "POST",
            "endpoint": search_bills,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/bills/download",
            "method": "POST",
            "endpoint": download_bills,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/bills/generate",
            "method": "POST",
            "endpoint": generate_bills,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/bills/{bill_id}",
            "method": "GET",
            "endpoint": get_bill,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # {
        #     'path': '/billing-system/api/v1/bills/{bill_id}',
        #     'method': 'PUT',
        #     'endpoint': update_bill,
        #     "public": False,
        #     'roles': {'admin', 'system'},
        #     'rate_limit': {'requests_per_minute': 10, 'requests_per_hour': 100, 'requests_per_day': 1000}
        # },
        {
            'path': '/billing-system/api/v1/bills/{bill_id}',
            'method': 'DELETE',
            'endpoint': delete_bill,
            "public": False,
            'roles': {'admin', 'system'},
            'rate_limit': {'requests_per_minute': 10, 'requests_per_hour': 100, 'requests_per_day': 1000}
        },
        # Fixes routes
        {
            "path": "/billing-system/api/v1/fixes/search",
            "method": "POST",
            "endpoint": search_fixes,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/fixes/create",
            "method": "POST",
            "endpoint": create_fix,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/fixes/delete",
            "method": "DELETE",
            "endpoint": delete_fixes,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/fixes/{fix_id}",
            "method": "GET",
            "endpoint": get_fix,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/fixes/{fix_id}",
            "method": "PUT",
            "endpoint": update_fix,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Templates routes
        {
            "path": "/billing-system/api/v1/templates/create",
            "method": "POST",
            "endpoint": create_template,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/templates/search",
            "method": "POST",
            "endpoint": search_templates,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 100, "requests_per_hour": 1000, "requests_per_day": 24000}
        },
        {
            "path": "/billing-system/api/v1/templates/{template_id}",
            "method": "GET",
            "endpoint": get_template,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/templates/{template_id}",
            "method": "PUT",
            "endpoint": update_template,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/templates/{template_id}",
            "method": "DELETE",
            "endpoint": delete_template,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Dashboard routes
        {
            "path": "/billing-system/api/v1/dashboard/summary",
            "method": "GET",
            "endpoint": get_dashboard_summary,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Messages routes
        {
            "path": "/billing-system/api/v1/messages/send-messages",
            "method": "POST",
            "endpoint": send_messages,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Whatsapp Session Routes
        {
            "path": "/billing-system/api/v1/session/create",
            "method": "POST",
            "endpoint": create_session,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/session/delete",
            "method": "DELETE",
            "endpoint": delete_session,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/session/status",
            "method": "GET",
            "endpoint": get_session_status,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/session/connect",
            "method": "GET",
            "endpoint": connect_session,
            "public": False,
            "roles": {"admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/session/webhook",
            "method": "POST",
            "endpoint": handle_webhook_events,
            "public": True,
            "roles": {"user","admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/session/webhook/events",
            "method": "GET",
            "endpoint": get_webhook_events,
            "public": True,
            "roles": {"user","admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # celery
        {
            "path": "/billing-system/api/v1/tasks/{task_id}/status",
            "method": "GET",
            "endpoint": get_task_status,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        # Payments
        {
            "path": "/billing-system/api/v1/payments/create",
            "method": "POST",
            "endpoint": create_payment,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/payments/all",
            "method": "GET",
            "endpoint": get_all_payments_by_bill_id,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/payments/mark-as-paid",
            "method": "POST",
            "endpoint": mark_all_bills_as_paid,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/payments/{payment_id}",
            "method": "GET",
            "endpoint": get_payment_by_id,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/payments/{payment_id}",
            "method": "PUT",
            "endpoint": update_payment,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        {
            "path": "/billing-system/api/v1/payments/{payment_id}",
            "method": "DELETE",
            "endpoint": delete_payment,
            "public": False,
            "roles": {"user", "admin", "system"},
            "rate_limit": {"requests_per_minute": 10, "requests_per_hour": 100, "requests_per_day": 1000}
        },
        
    ]
    # Build optimized lookup structures
    route_config = {}
    
    for route_def in routes:
        # Create lookup key
        key = f"{route_def['method']}:{route_def['path']}"
        
        # Store config for fast lookup
        route_config[key] = {
            "public": route_def["public"],
            "roles": route_def["roles"],
            "rate_limit": route_def["rate_limit"],
            "route": Route(
                route_def["path"], 
                methods=[route_def["method"]], 
                endpoint=route_def["endpoint"]
            )
        }
        
    logger.info("Routes configuration created successfully.")
    
    return route_config


ROUTE_CONFIG = create_routes_config()

