from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from db import db
from models.global_setting import GlobalSetting
from models.work_session import WorkSession
from schemas.work_session_schema import WorkSessionSchema
from sqlalchemy.sql import func, text, case, cast
from sqlalchemy import Date
import csv
from io import StringIO
from utils.datetime_utils import LOCAL_TZ

work_session_bp = Blueprint("work_session_bp", __name__, url_prefix="/work_sessions")
work_session_schema = WorkSessionSchema()
work_session_list_schema = WorkSessionSchema(many=True)

DEFAULT_DAILY_TARGET_TIME = "09:00:00"


def _parse_hhmmss_to_seconds(value):
    try:
        hours_str, minutes_str, seconds_str = str(value).split(":")
        hours = int(hours_str)
        minutes = int(minutes_str)
        seconds = int(seconds_str)
        if minutes < 0 or minutes > 59 or seconds < 0 or seconds > 59 or hours < 0:
            raise ValueError
        return hours * 3600 + minutes * 60 + seconds
    except Exception:
        return _parse_hhmmss_to_seconds(DEFAULT_DAILY_TARGET_TIME)


def _get_daily_target_time():
    setting = GlobalSetting.query.filter_by(
        key="work_session_daily_target_time",
        is_active=True,
    ).first()
    if not setting or not setting.value:
        return DEFAULT_DAILY_TARGET_TIME
    return str(setting.value).strip() or DEFAULT_DAILY_TARGET_TIME


def _local_date_range_to_utc(start_date_str, end_date_str):
    start_local_naive = datetime.strptime(start_date_str, "%Y-%m-%d").replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_local_naive = datetime.strptime(end_date_str, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59, microsecond=999999
    )

    start_local = LOCAL_TZ.localize(start_local_naive)
    end_local = LOCAL_TZ.localize(end_local_naive)

    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


@work_session_bp.route("/start", methods=["POST"])
@jwt_required()
def start_work_session():
    user_id = get_jwt_identity()
    if WorkSession.query.filter_by(user_id=user_id, status="IN_PROGRESS").first():
        return jsonify({"message": "Ya tienes una jornada en curso."}), 400

    new_session = WorkSession(user_id=user_id, login_time=datetime.utcnow().replace(microsecond=0))
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

    session.logout_time = datetime.utcnow().replace(microsecond=0)
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

    session.logout_time = datetime.utcnow().replace(microsecond=0)
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
            start_utc, end_utc = _local_date_range_to_utc(start_date_str, end_date_str)
            query = query.filter(WorkSession.login_time >= start_utc, WorkSession.login_time <= end_utc)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    sessions = query.order_by(WorkSession.id.desc()).all()
    return jsonify(work_session_list_schema.dump(sessions)), 200

@work_session_bp.route("/latest", methods=["GET"])
@jwt_required()
def get_latest_work_session():
    user_id = get_jwt_identity()
    session = WorkSession.query.filter_by(user_id=user_id).order_by(WorkSession.id.desc()).first()
    if not session:
        return jsonify({"message": "No hay sesiones registradas"}), 404
    return jsonify({"session": work_session_schema.dump(session)}), 200

@work_session_bp.route("/report", methods=["GET"])
@jwt_required()
def work_sessions_report():
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    download_csv = request.args.get("download_csv", "false").lower() == "true"

    if not start_date_str or not end_date_str:
        return jsonify({
            "error": "start_date y end_date son obligatorios (formato YYYY-MM-DD)"
        }), 400

    try:
        start_utc, end_utc = _local_date_range_to_utc(start_date_str, end_date_str)
    except ValueError:
        return jsonify({
            "error": "Formato de fecha inválido. Usa YYYY-MM-DD"
        }), 400

    report_data = _fetch_work_sessions_report(start_utc, end_utc)
    return _generate_csv_report(report_data, start_date_str, end_date_str) if download_csv else _generate_json_report(report_data)

def _fetch_work_sessions_report(start_utc, end_utc):
    from models.user import User

    daily_target_time = _get_daily_target_time()
    jornada_standard_sec = _parse_hhmmss_to_seconds(daily_target_time)
    sessions = (
        db.session.query(
            WorkSession.user_id,
            User.name.label("nombre_usuario"),
            func.count(WorkSession.id).label("total_sesiones"),
            func.sec_to_time(func.sum(func.time_to_sec(func.timediff(WorkSession.logout_time, WorkSession.login_time)))).label("total_duracion"),
            func.sec_to_time(func.sum(case(
                (func.timediff(WorkSession.logout_time, WorkSession.login_time) > text(f"'{daily_target_time}'"),
                 func.time_to_sec(func.timediff(WorkSession.logout_time, WorkSession.login_time)) - jornada_standard_sec),
                else_=0
            ))).label("total_extra"),
            func.sec_to_time(func.sum(case(
                (func.timediff(WorkSession.logout_time, WorkSession.login_time) < text(f"'{daily_target_time}'"),
                 jornada_standard_sec - func.time_to_sec(func.timediff(WorkSession.logout_time, WorkSession.login_time))),
                else_=0
            ))).label("total_faltante"),
        )
        .join(User, WorkSession.user_id == User.id)
        .filter(
            WorkSession.login_time >= start_utc,
            WorkSession.login_time <= end_utc,
            WorkSession.logout_time.isnot(None)
        )
        .group_by(WorkSession.user_id, User.name)
        .order_by(WorkSession.user_id)
        .all()
    )

    return [
        {
            "user_id": s.user_id,
            "nombre_usuario": s.nombre_usuario,
            "total_sesiones": s.total_sesiones,
            "total_duracion": str(s.total_duracion),
            "total_extra": str(s.total_extra),
            "total_faltante": str(s.total_faltante)
        }
        for s in sessions
    ]

def _generate_json_report(report_data):
    return jsonify({
        "daily_target_time": _get_daily_target_time(),
        "report": report_data,
    }), 200

def _generate_csv_report(report_data, start_date_str, end_date_str):
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["User ID", "Nombre Usuario", "Total Sesiones", "Total Duracion", "Total Extra", "Total Faltante"])
    for row in report_data:
        cw.writerow([
            row["user_id"],
            row["nombre_usuario"],
            row["total_sesiones"],
            row["total_duracion"],
            row["total_extra"],
            row["total_faltante"]
        ])
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=reporte_{start_date_str}_a_{end_date_str}.csv"}
    )
