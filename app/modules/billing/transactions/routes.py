from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
import calendar
from db import db
from models.transaction import Transaction
from models.user import User
from models.payment_type import PaymentType
from models.transaction_category import TransactionCategory
from models.client import Client
from schemas.transaction_schema import TransactionSchema
from sqlalchemy.orm import joinedload

transaction_bp = Blueprint("transaction_bp", __name__, url_prefix="/transactions")
transaction_schema = TransactionSchema()
transaction_list_schema = TransactionSchema(many=True)


@transaction_bp.route("/<int:transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id):
    trans = Transaction.query.options(
        joinedload(Transaction.client),
        joinedload(Transaction.category),
        joinedload(Transaction.payment_type),
        joinedload(Transaction.user)
    ).get_or_404(transaction_id)
    return jsonify(transaction_schema.dump(trans)), 200


@transaction_bp.route("", methods=["GET"])
@jwt_required()
def get_all_transactions():
    user_id = request.args.get("user_id", default=None)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    # Paginación
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    # Fechas
    if start_date_str and end_date_str:
        try:
            parsed_start = datetime.strptime(start_date_str, "%Y-%m-%d")
            parsed_end = datetime.strptime(end_date_str, "%Y-%m-%d")

            start_date = parsed_start.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = parsed_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        now = datetime.utcnow()
        year = now.year
        month = now.month
        _, last_day_of_month = calendar.monthrange(year, month)

        start_date = datetime(year, month, 1, 0, 0, 0, 0)
        end_date = datetime(year, month, last_day_of_month, 23, 59, 59, 999999)

    query = Transaction.query.options(
        joinedload(Transaction.client),
        joinedload(Transaction.category),
        joinedload(Transaction.payment_type),
        joinedload(Transaction.user)
    )

    if user_id == "":
        user_id = None

    if user_id is not None:
        user_id = int(user_id)
        query = query.filter_by(user_id=user_id)

    query = query.filter(
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date
    ).order_by(Transaction.created_at.desc())

    # Paginado con SQLAlchemy paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": transaction_list_schema.dump(pagination.items),
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page
    }), 200


@transaction_bp.route("", methods=["POST"])
@jwt_required()
def create_transaction():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = transaction_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Validar User
    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": f"User with id {data['user_id']} not found"}), 404

    # Validar Payment Type
    p_type = PaymentType.query.get(data["payment_type_id"])
    if not p_type:
        return jsonify({"error": f"PaymentType with id {data['payment_type_id']} not found"}), 404

    # Validar Category si es OUT
    if data["transaction_type"] == "OUT":
        if "category_id" in data and data["category_id"] is not None:
            category = TransactionCategory.query.get(data["category_id"])
            if not category:
                return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404
        client_id = None
    else:
        # IN: client_id es obligatorio
        if "client_id" not in data or data["client_id"] is None:
            return jsonify({"error": "client_id is required for IN transactions"}), 400
        client = Client.query.get(data["client_id"])
        if not client:
            return jsonify({"error": f"Client with id {data['client_id']} not found"}), 404
        client_id = data["client_id"]

    new_trans = Transaction(
        user_id=data["user_id"],
        transaction_type=data["transaction_type"],
        payment_type_id=data["payment_type_id"],
        category_id=data.get("category_id") if data["transaction_type"] == "OUT" else None,
        client_id=client_id,
        detail=data.get("detail"),
        amount=data["amount"]
    )

    db.session.add(new_trans)
    db.session.commit()

    return jsonify({
        "message": "Transaction created",
        "transaction": transaction_schema.dump(new_trans)
    }), 201


@transaction_bp.route("/<int:transaction_id>", methods=["PUT"])
@jwt_required()
def update_transaction(transaction_id):
    trans = Transaction.query.get_or_404(transaction_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = transaction_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Actualizar user
    if "user_id" in data:
        user = User.query.get(data["user_id"])
        if not user:
            return jsonify({"error": f"User with id {data['user_id']} not found"}), 404
        trans.user_id = data["user_id"]

    if "payment_type_id" in data:
        p_type = PaymentType.query.get(data["payment_type_id"])
        if not p_type:
            return jsonify({"error": f"PaymentType with id {data['payment_type_id']} not found"}), 404
        trans.payment_type_id = data["payment_type_id"]

    if "transaction_type" in data:
        trans.transaction_type = data["transaction_type"]

    # Transaction type puede haber cambiado:
    if trans.transaction_type == "OUT":
        # OUT: category_id opcional, client_id debe ser None
        if "category_id" in data:
            if data["category_id"] is not None:
                category = TransactionCategory.query.get(data["category_id"])
                if not category:
                    return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404
            trans.category_id = data["category_id"]
        trans.client_id = None
    else:
        # IN: category_id debe quedar en None, client_id obligatorio
        trans.category_id = None
        if "client_id" in data:
            if data["client_id"] is None:
                return jsonify({"error": "client_id is required for IN transactions"}), 400
            client = Client.query.get(data["client_id"])
            if not client:
                return jsonify({"error": f"Client with id {data['client_id']} not found"}), 404
            trans.client_id = data["client_id"]

    if "detail" in data:
        trans.detail = data["detail"]

    if "amount" in data:
        trans.amount = data["amount"]

    db.session.commit()
    return jsonify({
        "message": "Transaction updated",
        "transaction": transaction_schema.dump(trans)
    }), 200
