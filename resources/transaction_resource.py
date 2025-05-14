from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
import calendar
from db import db
from models.transaction import Transaction
from models.user import User
from models.payment_type import PaymentType
from models.transaction_category import TransactionCategory
from schemas.transaction_schema import TransactionSchema

transaction_bp = Blueprint("transaction_bp", __name__, url_prefix="/transactions")
transaction_schema = TransactionSchema()
transaction_list_schema = TransactionSchema(many=True)

@transaction_bp.route("/<int:transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id):
    trans = Transaction.query.get_or_404(transaction_id)
    if trans.transaction_type == "OUT" and trans.category_id:
        category = TransactionCategory.query.get(trans.category_id)
        trans.category_name = category.category_name if category else None
    return jsonify(transaction_schema.dump(trans)), 200


@transaction_bp.route("", methods=["GET"])
@jwt_required()
def get_all_transactions():
    user_id = request.args.get("user_id", default=None)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

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

    query = Transaction.query

    if user_id == "":
        user_id = None

    if user_id is not None:
        user_id = int(user_id)
        query = query.filter_by(user_id=user_id)

    query = query.filter(
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date
    )

    query = query.order_by(Transaction.created_at.desc())
    transactions = query.all()

    # Agregar el nombre de la categoría solo para transacciones OUT
    for transaction in transactions:
        if transaction.transaction_type == 'OUT' and transaction.category_id:
            category = TransactionCategory.query.get(transaction.category_id)
            transaction.category_name = category.category_name if category else None
    return jsonify(transaction_list_schema.dump(transactions)), 200


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

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": f"User with id {data['user_id']} not found"}), 404

    p_type = PaymentType.query.get(data["payment_type_id"])
    if not p_type:
        return jsonify({"error": f"PaymentType with id {data['payment_type_id']} not found"}), 404

    # Validar categoría solo si está presente y no es None
    if "category_id" in data and data["category_id"] is not None:
        category = TransactionCategory.query.get(data["category_id"])
        if not category:
            return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404

    new_trans = Transaction(
        user_id=data["user_id"],
        transaction_type=data["transaction_type"],
        payment_type_id=data["payment_type_id"],
        category_id=data.get("category_id"),  # puede ser None y está bien
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

    if "user_id" in data:
        user = User.query.get(data["user_id"])
        if not user:
            return jsonify({"error": f"User with id {data['user_id']} not found"}), 404
        trans.user_id = data["user_id"]

    if "transaction_type" in data:
        trans.transaction_type = data["transaction_type"]

    if "payment_type_id" in data:
        p_type = PaymentType.query.get(data["payment_type_id"])
        if not p_type:
            return jsonify({"error": f"PaymentType with id {data['payment_type_id']} not found"}), 404
        trans.payment_type_id = data["payment_type_id"]

    if "category_id" in data:
        category = TransactionCategory.query.get(data["category_id"])
        if not category:
            return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404
        trans.category_id = data["category_id"]

    if "detail" in data:
        trans.detail = data["detail"]

    if "amount" in data:
        trans.amount = data["amount"]

    db.session.commit()
    return jsonify({"message": "Transaction updated", "transaction": transaction_schema.dump(trans)}), 200
