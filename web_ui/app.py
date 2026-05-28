from flask import Flask, jsonify, request
import os
import time
from web_ui.conf import logger, REPORT_DIR, running_tasks
from web_ui.get_case import case_bp
from web_ui.list_report import list_report_bp
from web_ui.list_screenshots import list_screenshots_bp
from web_ui.run import run_bp
from web_ui.task import task_bp
from web_ui.upload import upload_bp
from web_ui.api import api_bp
from web_ui.ui import ui_test_bp

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False
app.register_blueprint(case_bp)
app.register_blueprint(task_bp)
app.register_blueprint(run_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(list_report_bp)
app.register_blueprint(list_screenshots_bp)
app.register_blueprint(api_bp)
app.register_blueprint(ui_test_bp)


if not os.path.exists(REPORT_DIR):
    logger.warning(f"报告目录不存在，将创建：{REPORT_DIR}")
    os.makedirs(REPORT_DIR, exist_ok=True)
else:
    logger.info(f"报告目录已存在：{REPORT_DIR}")
    logger.info(f"目录中的文件：{os.listdir(REPORT_DIR)}")


@app.before_request
def log_request_info():
    request.start_time = time.time()
    logger.info("=" * 80)
    logger.info(f" 请求开始: {request.method} {request.path}")
    logger.info(f" 客户端 IP: {request.remote_addr}")
    if request.args:
        logger.info(f"查询参数: {dict(request.args)}")
    if request.is_json:
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                logger.info(f" 请求体: {json_data}")
        except Exception as e:
            logger.warning(f"无法解析请求体: {e}")
    elif request.form:
        logger.info(f" 表单数据: {dict(request.form)}")


@app.after_request
def log_response_info(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        duration_ms = round(duration * 1000, 2)
    else:
        duration_ms = 0
    logger.info(f"响应状态: {response.status_code}")
    logger.info(f"处理时间: {duration_ms}ms")
    if response.content_type:
        logger.info(f"内容类型: {response.content_type}")
    if response.status_code >= 400:
        logger.warning(f"错误响应: {response.status_code} - {request.method} {request.path}")
    logger.info("=" * 80)
    return response


@app.errorhandler(404)
def handle_404(error):
    logger.warning(f"错误: {request.method} {request.path}")
    return jsonify({'success': False, 'message': '资源不存在'}), 404


@app.errorhandler(500)
def handle_500(error):
    logger.exception(f"服务器错误: {request.method} {request.path}\n错误详情: {str(error)}")
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)
