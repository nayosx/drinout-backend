from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.work_session import WorkSession
from schemas.work_session_schema import WorkSessionSchema
from datetime import datetime
import pytz
from sqlalchemy.sql import func

SV_TZ = pytz.timezone("America/El_Salvador")

work_session_bp = Blueprint("work_session_bp", __name__, url_prefix="/work_sessions")
work_session_schema = WorkSessionSchema()
work_session_list_schema = WorkSessionSchema(many=True)

@work_session_bp.route("/start", methods=["POST"])
@jwt_required()
def start_work_session():
    user_id = get_jwt_identity()

    existing_session = WorkSession.query.filter_by(user_id=user_id, status="IN_PROGRESS").first()
    if existing_session:
        return jsonify({"message": "Ya tienes una jornada en curso."}), 400

    new_session = WorkSession(user_id=user_id, login_time=datetime.now(SV_TZ).replace(microsecond=0))
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"message": "Jornada iniciada", "session": work_session_schema.dump(new_session)}), 201

@work_session_bp.route("/end", methods=["POST"])
@jwt_required()
def end_work_session():
    user_id = get_jwt_identity()

    session = WorkSession.query.filter_by(user_id=user_id, status="IN_PROGRESS").first()
    if not session:
        return jsonify({"message": "No tienes una jornada activa."}), 400

    session.logout_time = datetime.now(SV_TZ).replace(microsecond=0)
    session.status = "COMPLETED"
    db.session.commit()
    
    return jsonify({"message": "Jornada finalizada", "session": work_session_schema.dump(session)}), 200

@work_session_bp.route("/force_end", methods=["POST"])
@jwt_required()
def force_end_work_session():
    user_id = request.json.get("user_id")
    comments = request.json.get("comments", "")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    session = WorkSession.query.filter_by(user_id=user_id, status="IN_PROGRESS").first()
    if not session:
        return jsonify({"error": "No active session found for this user"}), 404

    session.logout_time = datetime.now(SV_TZ).replace(microsecond=0)
    session.status = "COMPLETED"
    session.comments = comments
    db.session.commit()

    return jsonify({"message": "Work session forcibly closed", "session": work_session_schema.dump(session)}), 200

@work_session_bp.route("", methods=["GET"])
@jwt_required()
def get_work_sessions():
    user_id = request.args.get("user_id", type=int)
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    query = WorkSession.query

    if user_id:
        query = query.filter_by(user_id=user_id)

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)

            query = query.filter(
                WorkSession.login_time >= start_date,
                WorkSession.login_time <= end_date
            )
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    sessions = query.all()
    return jsonify(work_session_list_schema.dump(sessions)), 200

@work_session_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_work_session():
    user_id = get_jwt_identity()

    session = WorkSession.query.filter_by(user_id=user_id).order_by(WorkSession.login_time.desc()).first()

    if not session:
        return jsonify({"message": "No hay sesiones registradas"}), 404

    return jsonify({"session": work_session_schema.dump(session)}), 200
