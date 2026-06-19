import calendar
from datetime import date, datetime, time, timezone
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import case, extract, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from db import db
from models.client import Client
from models.payment_type import PaymentType
from models.transaction import Transaction
from models.transaction_category import TransactionCategory
from models.user import User
from schemas.transaction_fortnight_summary_schema import (
    TransactionFortnightSummarySchema,
)
from schemas.transaction_schema import TransactionSchema
from utils.datetime_utils import LOCAL_TZ, localize_naive

transaction_bp = Blueprint("transaction_bp", __name__, url_prefix="/transactions")
transaction_schema = TransactionSchema()
transaction_list_schema = TransactionSchema(many=True)
transaction_fortnight_summary_schema = TransactionFortnightSummarySchema()

LIST_DATE_FORMAT = "%Y-%m-%d"
SUMMARY_DATE_FORMAT = "%d-%m-%Y"
ZERO_AMOUNT = Decimal("0.00")


def _get_current_month_range():
    local_now = datetime.now(LOCAL_TZ).date()
    _, last_day = calendar.monthrange(local_now.year, local_now.month)
    return date(local_now.year, local_now.month, 1), date(local_now.year, local_now.month, last_day)


def _get_current_utc_month_datetime_range():
    now = datetime.utcnow()
    _, last_day = calendar.monthrange(now.year, now.month)
    start_date = datetime(now.year, now.month, 1, 0, 0, 0, 0)
    end_date = datetime(now.year, now.month, last_day, 23, 59, 59, 999999)
    return start_date, end_date


def _parse_list_date_range(start_date_str, end_date_str):
    parsed_start = datetime.strptime(start_date_str, LIST_DATE_FORMAT)
    parsed_end = datetime.strptime(end_date_str, LIST_DATE_FORMAT)

    start_date = parsed_start.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = parsed_end.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_date, end_date


def _parse_summary_date_range(start_date_str, end_date_str):
    start_local_date = datetime.strptime(start_date_str, SUMMARY_DATE_FORMAT).date()
    end_local_date = datetime.strptime(end_date_str, SUMMARY_DATE_FORMAT).date()

    if start_local_date > end_local_date:
        raise ValueError("start_date cannot be greater than end_date")

    return start_local_date, end_local_date


def _local_date_range_to_utc(start_local_date, end_local_date):
    start_local_naive = datetime.combine(start_local_date, time.min)
    end_local_naive = datetime.combine(end_local_date, time.max)

    start_utc = localize_naive(start_local_naive).astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = localize_naive(end_local_naive).astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def _get_user_id_filter(raw_user_id):
    if raw_user_id in (None, ""):
        return None

    try:
        return int(raw_user_id)
    except (TypeError, ValueError):
        raise ValueError("user_id must be an integer")


def _format_summary_date(value):
    return value.strftime(SUMMARY_DATE_FORMAT)


def _increment_month(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _build_fortnight_buckets(start_local_date, end_local_date):
    buckets = []
    year = start_local_date.year
    month = start_local_date.month

    while (year, month) <= (end_local_date.year, end_local_date.month):
        _, last_day = calendar.monthrange(year, month)
        fortnight_ranges = (
            (1, date(year, month, 1), date(year, month, 15)),
            (2, date(year, month, 16), date(year, month, last_day)),
        )

        for fortnight, bucket_start, bucket_end in fortnight_ranges:
            if bucket_end < start_local_date or bucket_start > end_local_date:
                continue

            buckets.append(
                {
                    "year": year,
                    "month": month,
                    "fortnight": fortnight,
                    "label": f"{_format_summary_date(bucket_start)} al {_format_summary_date(bucket_end)}",
                    "bucket_start_date": _format_summary_date(bucket_start),
                    "bucket_end_date": _format_summary_date(bucket_end),
                }
            )

        year, month = _increment_month(year, month)

    return buckets


def _local_utc_offset_string():
    offset = datetime.now(LOCAL_TZ).utcoffset()
    if offset is None:
        return "+00:00"

    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _local_created_at_expression():
    bind = db.session.get_bind(mapper=Transaction.__mapper__)
    dialect = bind.dialect.name if bind is not None else None
    offset = _local_utc_offset_string()

    if dialect == "mysql":
        return func.convert_tz(Transaction.created_at, "+00:00", offset)

    if dialect == "sqlite":
        sign = "-" if offset.startswith("-") else "+"
        hours = offset[1:3]
        minutes = offset[4:6]
        return func.datetime(Transaction.created_at, f"{sign}{hours} hours", f"{sign}{minutes} minutes")

    return Transaction.created_at


def _normalize_amount(value):
    if value is None:
        return ZERO_AMOUNT
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _get_fortnight_aggregates(start_utc, end_utc, user_id=None):
    local_created_at = _local_created_at_expression()
    year_expr = extract("year", local_created_at)
    month_expr = extract("month", local_created_at)
    fortnight_expr = case((extract("day", local_created_at) <= 15, 1), else_=2)

    query = db.session.query(
        year_expr.label("year"),
        month_expr.label("month"),
        fortnight_expr.label("fortnight"),
        func.coalesce(
            func.sum(case((Transaction.transaction_type == "IN", Transaction.amount), else_=0)),
            0,
        ).label("in_total"),
        func.coalesce(
            func.sum(case((Transaction.transaction_type == "OUT", Transaction.amount), else_=0)),
            0,
        ).label("out_total"),
    ).filter(
        Transaction.created_at >= start_utc,
        Transaction.created_at <= end_utc,
    )

    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)

    rows = (
        query.group_by(year_expr, month_expr, fortnight_expr)
        .order_by(year_expr, month_expr, fortnight_expr)
        .all()
    )

    aggregates = {}
    for row in rows:
        key = (int(row.year), int(row.month), int(row.fortnight))
        aggregates[key] = {
            "in_total": _normalize_amount(row.in_total),
            "out_total": _normalize_amount(row.out_total),
        }

    return aggregates


def _build_fortnight_summary_items(start_local_date, end_local_date, user_id=None):
    start_utc, end_utc = _local_date_range_to_utc(start_local_date, end_local_date)
    aggregates = _get_fortnight_aggregates(start_utc, end_utc, user_id=user_id)
    items = []

    for bucket in _build_fortnight_buckets(start_local_date, end_local_date):
        key = (bucket["year"], bucket["month"], bucket["fortnight"])
        aggregate = aggregates.get(key, {"in_total": ZERO_AMOUNT, "out_total": ZERO_AMOUNT})
        items.append(
            {
                **bucket,
                "in_total": aggregate["in_total"],
                "out_total": aggregate["out_total"],
            }
        )

    return items


@transaction_bp.route("/<int:transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id):
    trans = Transaction.query.options(
        joinedload(Transaction.client),
        joinedload(Transaction.category),
        joinedload(Transaction.payment_type),
        joinedload(Transaction.user),
    ).get_or_404(transaction_id)
    return jsonify(transaction_schema.dump(trans)), 200


@transaction_bp.route("/fortnight-summary", methods=["GET"])
@jwt_required()
def get_transaction_fortnight_summary():
    user_id_str = request.args.get("user_id")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        user_id = _get_user_id_filter(user_id_str)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if bool(start_date_str) ^ bool(end_date_str):
        return jsonify(
            {"error": "start_date and end_date are required together. Use dd-mm-yyyy"}
        ), 400

    if start_date_str and end_date_str:
        try:
            start_local_date, end_local_date = _parse_summary_date_range(
                start_date_str,
                end_date_str,
            )
        except ValueError as exc:
            message = str(exc)
            if message == "start_date cannot be greater than end_date":
                return jsonify({"error": message}), 400
            return jsonify({"error": "Invalid date format. Use dd-mm-yyyy"}), 400
    else:
        start_local_date, end_local_date = _get_current_month_range()

    payload = {
        "range": {
            "start_date": _format_summary_date(start_local_date),
            "end_date": _format_summary_date(end_local_date),
        },
        "filters": {"user_id": user_id},
        "items": _build_fortnight_summary_items(
            start_local_date,
            end_local_date,
            user_id=user_id,
        ),
    }
    return jsonify(transaction_fortnight_summary_schema.dump(payload)), 200


@transaction_bp.route("", methods=["GET"])
@jwt_required()
def get_all_transactions():
    user_id = request.args.get("user_id", default=None)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    if start_date_str and end_date_str:
        try:
            start_date, end_date = _parse_list_date_range(start_date_str, end_date_str)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    else:
        start_date, end_date = _get_current_utc_month_datetime_range()

    query = Transaction.query.options(
        joinedload(Transaction.client),
        joinedload(Transaction.category),
        joinedload(Transaction.payment_type),
        joinedload(Transaction.user),
    )

    if user_id == "":
        user_id = None

    if user_id is not None:
        query = query.filter_by(user_id=int(user_id))

    query = query.filter(
        Transaction.created_at >= start_date,
        Transaction.created_at <= end_date,
    ).order_by(Transaction.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": transaction_list_schema.dump(pagination.items),
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
        }
    ), 200


@transaction_bp.route("", methods=["POST"])
@jwt_required()
def create_transaction():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = transaction_schema.load(json_data)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    idempotency_key = request.headers.get("Idempotency-Key")

    if idempotency_key:
        existing = Transaction.query.filter_by(idempotency_key=idempotency_key).first()
        if existing:
            return jsonify(
                {
                    "message": "Transaction already processed",
                    "transaction": transaction_schema.dump(existing),
                }
            ), 200

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": f"User with id {data['user_id']} not found"}), 404

    payment_type = PaymentType.query.get(data["payment_type_id"])
    if not payment_type:
        return jsonify({"error": f"PaymentType with id {data['payment_type_id']} not found"}), 404

    if data["transaction_type"] == "OUT":
        if "category_id" in data and data["category_id"] is not None:
            category = TransactionCategory.query.get(data["category_id"])
            if not category:
                return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404
        client_id = None
    else:
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
        amount=data["amount"],
        idempotency_key=idempotency_key,
    )

    db.session.add(new_trans)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = Transaction.query.filter_by(idempotency_key=idempotency_key).first()
        return jsonify(
            {
                "message": "Transaction already processed",
                "transaction": transaction_schema.dump(existing),
            }
        ), 200

    return jsonify(
        {
            "message": "Transaction created",
            "transaction": transaction_schema.dump(new_trans),
        }
    ), 201


@transaction_bp.route("/<int:transaction_id>", methods=["PUT"])
@jwt_required()
def update_transaction(transaction_id):
    trans = Transaction.query.get_or_404(transaction_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        data = transaction_schema.load(json_data, partial=True)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    if "user_id" in data:
        user = User.query.get(data["user_id"])
        if not user:
            return jsonify({"error": f"User with id {data['user_id']} not found"}), 404
        trans.user_id = data["user_id"]

    if "payment_type_id" in data:
        payment_type = PaymentType.query.get(data["payment_type_id"])
        if not payment_type:
            return jsonify({"error": f"PaymentType with id {data['payment_type_id']} not found"}), 404
        trans.payment_type_id = data["payment_type_id"]

    if "transaction_type" in data:
        trans.transaction_type = data["transaction_type"]

    if trans.transaction_type == "OUT":
        if "category_id" in data:
            if data["category_id"] is not None:
                category = TransactionCategory.query.get(data["category_id"])
                if not category:
                    return jsonify({"error": f"Category with id {data['category_id']} not found"}), 404
            trans.category_id = data["category_id"]
        trans.client_id = None
    else:
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
    return jsonify(
        {
            "message": "Transaction updated",
            "transaction": transaction_schema.dump(trans),
        }
    ), 200
