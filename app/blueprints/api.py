from flask import Blueprint, jsonify
from ..models import Task

api_bp = Blueprint('api', __name__)

@api_bp.route('/tasks')
def api_tasks():
    tasks = Task.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'status': t.status.value,
        'reward': t.reward
    } for t in tasks])
