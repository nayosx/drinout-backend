from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from db import db
from models.transaction_category import TransactionCategory
from schemas.transaction_category import TransactionCategorySchema

transaction_category_bp = Blueprint('transaction_category_bp', __name__, url_prefix='/transaction-categories')
transaction_category_schema = TransactionCategorySchema()
transaction_categories_schema = TransactionCategorySchema(many=True)

@transaction_category_bp.route('', methods=['GET'])
@jwt_required()
def get_all_categories():
    categories = TransactionCategory.query.order_by(TransactionCategory.created_at.desc()).all()
    return jsonify(transaction_categories_schema.dump(categories)), 200

@transaction_category_bp.route('', methods=['POST'])
@jwt_required()
def create_category():
    json_data = request.get_json()
    if not json_data:
        return jsonify({'error': 'No input data provided'}), 400

    try:
        data = transaction_category_schema.load(json_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    new_category = TransactionCategory(category_name=data['category_name'])
    db.session.add(new_category)
    db.session.commit()

    return jsonify({'category': transaction_category_schema.dump(new_category)}), 201

@transaction_category_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    category = TransactionCategory.query.get_or_404(category_id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({'error': 'No input data provided'}), 400

    try:
        data = transaction_category_schema.load(json_data, partial=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if 'category_name' in data:
        category.category_name = data['category_name']

    db.session.commit()
    return jsonify({'message': 'Category updated', 'category': transaction_category_schema.dump(category)}), 200

@transaction_category_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    category = TransactionCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': f'Category {category_id} deleted'}), 200
