import os
from datetime import datetime

from flask import Blueprint, jsonify, request
from web_ui.conf import logger, REPORT_DIR, running_tasks
from web_ui.task import create_project_zip

run_bp = Blueprint('run', __name__)


@run_bp.route('/api/run', methods=['POST'])
def run_test():
    data = request.json
    test_name = data.get('test_name', 'test_ui')
    task_id = f"{test_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    logger.info(f"收到执行请求：{test_name}，任务 ID: {task_id}")

    zip_path = create_project_zip(task_id)

    running_tasks[task_id] = {
        'status': 'waiting_local',
        'success': None,
        'output': '任务已发布...',
        'report_path': None,
        'test_name': test_name
    }

    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务已发布'
    })
