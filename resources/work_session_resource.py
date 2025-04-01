from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models.work_session import WorkSession
from schemas.work_session_schema import WorkSessionSchema
from datetime import datetime
import pytz
from sqlalchemy.sql import func

import csv
from io import StringIO
from flask import Response

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

    query = query.order_by(WorkSession.id.desc())
    sessions = query.all()
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
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        return jsonify({
            "error": "Formato de fecha inválido. Usa YYYY-MM-DD"
        }), 400

    report_data = _fetch_work_sessions_report(start_date, end_date)

    if download_csv:
        return _generate_csv_report(report_data, start_date_str, end_date_str)
    else:
        return _generate_json_report(report_data)

def _fetch_work_sessions_report(start_date, end_date):
    from sqlalchemy import func, case, cast, Date, text
    from models.user import User

    jornada_standard_sec = 9 * 3600 + 30 * 60

    sessions = (
        db.session.query(
            WorkSession.user_id,
            User.name.label("nombre_usuario"),
            func.count(WorkSession.id).label("total_sesiones"),
            func.sec_to_time(func.sum(func.time_to_sec(func.timediff(WorkSession.logout_time, WorkSession.login_time)))).label("total_duracion"),
            func.sec_to_time(func.sum(case(
                (func.timediff(WorkSession.logout_time, WorkSession.login_time) > text("'09:30:00'"),
                 func.time_to_sec(func.timediff(WorkSession.logout_time, WorkSession.login_time)) - jornada_standard_sec),
                else_=0
            ))).label("total_extra"),
            func.sec_to_time(func.sum(case(
                (func.timediff(WorkSession.logout_time, WorkSession.login_time) < text("'09:30:00'"),
                 jornada_standard_sec - func.time_to_sec(func.timediff(WorkSession.logout_time, WorkSession.login_time))),
                else_=0
            ))).label("total_faltante"),
        )
        .join(User, WorkSession.user_id == User.id)
        .filter(
            cast(WorkSession.login_time, Date).between(start_date.date(), end_date.date()),
            WorkSession.logout_time.isnot(None)
        )
        .group_by(WorkSession.user_id, User.name)
        .order_by(WorkSession.user_id)
        .all()
    )

    report = [
        {
            "user_id": session.user_id,
            "nombre_usuario": session.nombre_usuario,
            "total_sesiones": session.total_sesiones,
            "total_duracion": str(session.total_duracion),
            "total_extra": str(session.total_extra),
            "total_faltante": str(session.total_faltante)
        }
        for session in sessions
    ]

    return report

def _generate_json_report(report_data):
    return jsonify({"report": report_data}), 200

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