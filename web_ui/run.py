import os
import zipfile
from datetime import datetime

from flask import Blueprint, jsonify, request
from web_ui.conf import logger, REPORT_DIR, running_tasks

run_bp = Blueprint('run', __name__)


@run_bp.route('/api/run', methods=['POST'])
def run_test():
    data = request.json
    test_name = data.get('test_name', 'test_ui')
    task_id = f"{test_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    logger.info(f"收到执行请求：{test_name}，任务 ID: {task_id}")

    # 1. 打包整个项目核心代码并保存到本地临时文件
    project_root = os.path.dirname(os.path.dirname(__file__))
    temp_dir = os.path.join(project_root, 'temp_zips')
    os.makedirs(temp_dir, exist_ok=True)

    zip_path = os.path.join(temp_dir, f"{task_id}.zip")
    exclude_dirs = {'__pycache__', '.idea', '.pytest_cache', 'reports', 'temp_tests', 'dist', 'build', 'temp_zips'}
    exclude_subdirs = {os.path.join('log', 'logger')}  # 只排除 log/logger 子目录

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            # 特殊处理：如果当前路径是 log/logger，则跳过
            current_relative_path = os.path.relpath(root, project_root)
            if current_relative_path in exclude_subdirs or any(
                    current_relative_path.startswith(excl + os.sep) for excl in exclude_subdirs):
                dirs.clear()
                continue

            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project_root)

                # 包含 Python 文件、配置文件和 requirements.txt
                if file.endswith(('.py', '.yml', '.yaml')) or file == 'requirements.txt':
                    zip_file.write(file_path, arcname)

    logger.info(f"项目包已保存: {zip_path}")

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
