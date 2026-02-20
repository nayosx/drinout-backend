from app.modules.health.routes import health_bp
from app.modules.users.routes import user_bp
from app.modules.auth.routes import auth_bp
from app.modules.billing.transactions.routes import transaction_bp
from app.modules.billing.payment_types.routes import payment_type_bp
from app.modules.operations.work_sessions.routes import work_session_bp
from app.modules.system_test.routes import test_bp
from app.modules.operations.tasks.routes import task_bp
from app.modules.menus.routes import menu_bp
from app.modules.roles.routes import role_bp
from app.modules.billing.transaction_categories.routes import transaction_category_bp
from app.modules.clients.routes import clients_bp
from app.modules.clients.address_routes import addresses_bp
from app.modules.clients.phone_routes import phones_bp
from app.modules.laundry.services.routes import laundry_service_bp
from app.modules.laundry.deliveries.routes import laundry_delivery_bp
from app.modules.laundry.processing_steps.routes import processing_step_bp
from app.modules.laundry.logs.routes import laundry_service_log_bp

from app.modules.laundry.queue.socket import register_laundry_queue_socket


def register_blueprints(app):
    app.register_blueprint(health_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_type_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(work_session_bp)
    app.register_blueprint(test_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(transaction_category_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(addresses_bp)
    app.register_blueprint(phones_bp)
    app.register_blueprint(laundry_service_bp)
    app.register_blueprint(laundry_delivery_bp)
    app.register_blueprint(processing_step_bp)
    app.register_blueprint(laundry_service_log_bp)


def register_sockets(socketio):
    register_laundry_queue_socket(socketio)
