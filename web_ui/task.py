import os
import zipfile

from flask import Blueprint, jsonify, request, send_file
from web_ui.conf import logger, REPORT_DIR, running_tasks

task_bp = Blueprint('task', __name__)


def create_project_zip(task_id):
    """
    打包项目核心代码为 ZIP 文件
    :param task_id: 任务 ID，用于命名 ZIP 文件
    :return: ZIP 文件的完整路径
    """
    project_root = os.path.dirname(os.path.dirname(__file__))
    temp_dir = os.path.join(project_root, 'temp_zips')
    os.makedirs(temp_dir, exist_ok=True)

    zip_path = os.path.join(temp_dir, f"{task_id}.zip")
    exclude_dirs = {'__pycache__', '.idea', '.pytest_cache', 'reports', 'temp_tests', 'dist', 'build', 'temp_zips'}
    exclude_subdirs = {os.path.join('log', 'logger')}

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            current_relative_path = os.path.relpath(root, project_root)
            if current_relative_path in exclude_subdirs or any(
                    current_relative_path.startswith(excl + os.sep) for excl in exclude_subdirs):
                dirs.clear()
                continue

            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, project_root)

                if file.endswith(('.py', '.yml', '.yaml', '.json')) or file == 'requirements.txt':
                    zip_file.write(file_path, arcname)

    logger.info(f"项目包已保存: {zip_path}")
    return zip_path


@task_bp.route('/api/poll_task')
def poll_task():
    """供本地客户端轮询领取任务"""
    pending_task_id = None
    pending_task = None

    for task_id, task_info in running_tasks.items():
        if task_info.get('status') == 'waiting_local':
            pending_task_id = task_id
            pending_task = task_info
            break

    if pending_task_id and pending_task:
        pending_task['status'] = 'executing'
        running_tasks[pending_task_id] = pending_task
        server_host = request.host_url.rstrip('/')
        return jsonify({
            'success': True,
            'data': {
                'task_id': pending_task_id,
                'test_name': pending_task.get('test_name'),
                'type': pending_task.get('type', 'pytest'),  # 新增：返回任务类型
                'download_url': f"{server_host}/api/get_task_zip/{pending_task_id}"
            }
        })

    return jsonify({'success': False, 'message': '无可用任务'})


@task_bp.route('/api/get_task_zip/<task_id>')
def get_task_zip(task_id):
    """提供指定任务的 ZIP 包下载"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    zip_path = os.path.join(project_root, 'temp_zips', f"{task_id}.zip")

    if os.path.exists(zip_path):
        logger.info(f"本地代理正在下载任务包: {task_id}.zip")
        try:
            return send_file(
                zip_path, 
                mimetype='application/zip', 
                as_attachment=True, 
                download_name=f"{task_id}.zip"
            )
        finally:
            os.remove(zip_path)
            logger.info(f"任务包已删除: {zip_path}")
    else:
        return jsonify({'success': False, 'message': '任务包不存在'}), 404


@task_bp.route('/api/status/<task_id>')
def get_status(task_id):
    logger.debug(f"查询任务状态：{task_id}")

    if task_id not in running_tasks:
        logger.warning(f"任务不存在：{task_id}")
        return jsonify({'success': False, 'message': '任务不存在'})

    task_info = running_tasks[task_id]
    logger.debug(f"任务 {task_id} 状态：{task_info['status']}")

    return jsonify({
        'success': True,
        'data': task_info
    })
