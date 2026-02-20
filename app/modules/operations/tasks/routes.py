from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.task import Task
from models.task_view import TaskView
from models.user import User  
from schemas.task_schema import TaskSchema, TaskViewSchema

task_bp = Blueprint("task_bp", __name__, url_prefix="/tasks")
task_schema = TaskSchema()
task_list_schema = TaskSchema(many=True)
task_view_schema = TaskViewSchema()

@task_bp.route("", methods=["GET"])
@jwt_required()
def get_all_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify(task_list_schema.dump(tasks)), 200

@task_bp.route("", methods=["POST"])
@jwt_required()
def create_task():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = task_schema.load(json_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": f"User with id {data['user_id']} not found"}), 404

    ws_id = data.get("work_session_id")
    if ws_id is not None:
        from models.work_session import WorkSession
        if not WorkSession.query.get(ws_id):
            return jsonify({"error": f"Work session with id {ws_id} not found"}), 404

    new_task = Task(
        user_id=data["user_id"],
        work_session_id=ws_id,
        description=data["description"]
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"task": task_schema.dump(new_task)}), 201


@task_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task_schema.dump(task)), 200

@task_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No input data provided"}), 400
    try:
        data = task_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if "description" in data:
        task.description = data["description"]
    if "user_id" in data:
        user = User.query.get(data["user_id"])
        if not user:
            return jsonify({"error": f"User with id {data['user_id']} not found"}), 404
        task.user_id = data["user_id"]
    db.session.commit()
    return jsonify({"message": "Task updated", "task": task_schema.dump(task)}), 200

@task_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": f"Task {task_id} deleted"}), 200

@task_bp.route("/<int:task_id>/views", methods=["POST"])
@jwt_required()
def add_task_view(task_id):
    json_data = request.get_json()
    if not json_data or "user_id" not in json_data:
        return jsonify({"error": "user_id is required in the request body"}), 400
    user_id = json_data["user_id"]

    task = Task.query.get_or_404(task_id)

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found"}), 404

    existing_view = TaskView.query.filter_by(task_id=task_id, user_id=user_id).first()
    if existing_view:
        return jsonify({"message": "View already recorded"}), 200

    new_view = TaskView(task_id=task_id, user_id=user_id)
    db.session.add(new_view)
    db.session.commit()
    return jsonify({"message": "Task view recorded", "task_view": task_view_schema.dump(new_view)}), 201
