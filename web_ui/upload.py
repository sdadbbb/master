import os

from flask import Blueprint, jsonify, request
from web_ui.conf import logger, REPORT_DIR, get_running_tasks

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/api/upload_report', methods=['POST'])
def upload_report():
    if 'report' not in request.files:
        logger.warning("未找到报告文件")
        return jsonify({'success': False, 'message': '未找到报告文件'})

    file = request.files['report']
    task_id = request.form.get('task_id')
    running_tasks = get_running_tasks()

    if task_id not in running_tasks:
        return jsonify({'success': False, 'message': '任务ID不存在或已过期'})

    filename = f"{task_id}_report.html"
    filepath = os.path.join(REPORT_DIR, filename)
    file.save(filepath)

    logger.info(f"收到来自本地的报告上传：{filename}")

    screenshot_count = 0
    for key in request.files:
        if key.startswith('screenshot_'):
            screenshot_file = request.files[key]
            screenshot_filename = screenshot_file.filename
            screenshot_path = os.path.join(REPORT_DIR, 'screenshots', screenshot_filename)
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            screenshot_file.save(screenshot_path)
            screenshot_count += 1
            logger.info(f"保存截图：{screenshot_filename}")

    log_count = 0
    for key in request.files:
        if key.startswith('log_'):
            log_file = request.files[key]
            log_filename = log_file.filename
            log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'log', 'logger', log_filename)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log_file.save(log_path)
            log_count += 1
            logger.info(f"保存日志：{log_filename}")

    running_tasks[task_id] = {
        'status': 'completed',
        'success': True,
        'output': f'本地执行成功，报告已上传（{screenshot_count}个截图，{log_count}个日志）',
        'report_path': filepath,
        'screenshot_count': screenshot_count,
        'log_count': log_count
    }

    # 5分钟后自动清理已完成的任务（给前端足够时间查询状态）
    import threading
    def cleanup_task():
        import time
        time.sleep(300)  # 5分钟
        if task_id in running_tasks:
            del running_tasks[task_id]
            logger.info(f"已清理完成任务: {task_id}")
    
    threading.Thread(target=cleanup_task, daemon=True).start()

    return jsonify({'success': True, 'message': '报告、截图和日志上传成功'})
