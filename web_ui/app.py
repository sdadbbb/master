from flask import Flask, render_template, jsonify, request, send_file
import subprocess
import os
import threading
from datetime import datetime
from multiprocessing import Manager  # 导入 Manager
import time
import zipfile
import io

from log.logger import LoggerUtil

# 创建 Flask 应用时指定模板编码
from util.file_util import FileUtil

manager = Manager()
running_tasks = manager.dict()
app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON

logger = LoggerUtil.get_logger()

REPORT_DIR = FileUtil.get_report_dir()

if not os.path.exists(REPORT_DIR):
    logger.warning(f"报告目录不存在，将创建：{REPORT_DIR}")
    os.makedirs(REPORT_DIR, exist_ok=True)
else:
    logger.info(f"报告目录已存在：{REPORT_DIR}")
    logger.info(f"目录中的文件：{os.listdir(REPORT_DIR)}")


@app.before_request
def log_request_info():
    """记录请求信息"""
    request.start_time = time.time()
    logger.info("=" * 80)
    logger.info(f" 请求开始: {request.method} {request.path}")
    logger.info(f" 客户端 IP: {request.remote_addr}")
    
    # 记录查询参数
    if request.args:
        logger.info(f"查询参数: {dict(request.args)}")
    
    # 记录请求体（JSON 数据）
    if request.is_json:
        try:
            json_data = request.get_json(silent=True)
            if json_data:
                logger.info(f" 请求体: {json_data}")
        except Exception as e:
            logger.warning(f"无法解析请求体: {e}")
    
    # 记录表单数据
    elif request.form:
        logger.info(f" 表单数据: {dict(request.form)}")


@app.after_request
def log_response_info(response):
    """记录响应信息"""
    # 计算请求处理时间
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        duration_ms = round(duration * 1000, 2)
    else:
        duration_ms = 0
    
    # 记录响应状态
    logger.info(f" 响应状态: {response.status_code}")
    logger.info(f"️  处理时间: {duration_ms}ms")
    
    # 记录响应内容类型
    if response.content_type:
        logger.info(f" 内容类型: {response.content_type}")
    
    # 对于错误响应，记录更多信息
    if response.status_code >= 400:
        logger.warning(f"  错误响应: {response.status_code} - {request.method} {request.path}")
    
    logger.info("=" * 80)
    
    return response


@app.errorhandler(404)
def handle_404(error):
    """处理 404 错误"""
    logger.warning(f"❌ 404 错误: {request.method} {request.path}")
    return jsonify({'success': False, 'message': '资源不存在'}), 404


@app.errorhandler(500)
def handle_500(error):
    """处理 500 错误"""
    logger.exception(f"💥 500 服务器错误: {request.method} {request.path}\n错误详情: {str(error)}")
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500


@app.route('/')
def index():
    logger.info("访问首页")
    return render_template('index.html')


@app.route('/api/tests')
def get_tests():
    logger.info("请求获取测试用例列表")
    test_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test')
    tests = []
    
    try:
        for file in os.listdir(test_dir):
            if file.startswith('test_') and file.endswith('.py'):
                tests.append({
                    'name': file[:-3],
                    'file': file
                })
        logger.info(f"找到 {len(tests)} 个测试用例：{[t['name'] for t in tests]}")
        return jsonify({'success': True, 'data': tests})
    except Exception as e:
        logger.exception(f"获取测试用例失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/run', methods=['POST'])
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
            if current_relative_path in exclude_subdirs or any(current_relative_path.startswith(excl + os.sep) for excl in exclude_subdirs):
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

@app.route('/api/poll_task')
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
                # 动态生成下载 URL
                'download_url': f"{server_host}/api/get_task_zip/{pending_task_id}"
            }
        })
    
    return jsonify({'success': False, 'message': '无可用任务'})

@app.route('/api/get_task_zip/<task_id>')
def get_task_zip(task_id):
    """提供指定任务的 ZIP 包下载"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    zip_path = os.path.join(project_root, 'temp_zips', f"{task_id}.zip")
    
    if os.path.exists(zip_path):
        logger.info(f"本地代理正在下载任务包: {task_id}.zip")
        return send_file(zip_path, mimetype='application/zip', as_attachment=True, download_name=f"{task_id}.zip")
    else:
        return jsonify({'success': False, 'message': '任务包不存在'}), 404

@app.route('/api/upload_report', methods=['POST'])
def upload_report():
    """接收本地代理执行后上传的报告、截图和日志"""
    if 'report' not in request.files:
        logger.warning("未找到报告文件")
        return jsonify({'success': False, 'message': '未找到报告文件'})
    
    file = request.files['report']
    task_id = request.form.get('task_id')
    
    if task_id not in running_tasks:
        return jsonify({'success': False, 'message': '任务ID不存在或已过期'})
        
    # 1. 保存报告文件
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
    
    # 4. 更新内存中的任务状态
    running_tasks[task_id] = {
        'status': 'completed',
        'success': True,
        'output': f'本地执行成功，报告已上传（{screenshot_count}个截图，{log_count}个日志）',
        'report_path': filepath,
        'screenshot_count': screenshot_count,
        'log_count': log_count
    }
            
    return jsonify({'success': True, 'message': '报告、截图和日志上传成功'})


@app.route('/api/status/<task_id>')
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


@app.route('/api/reports')
def list_reports():
    logger.info(f"获取报告列表，目录：{REPORT_DIR}")
    
    if not os.path.exists(REPORT_DIR):
        logger.error(f"报告目录不存在：{REPORT_DIR}")
        return jsonify({'success': False, 'message': f'报告目录不存在：{REPORT_DIR}'})
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    reports = []
    try:
        for file in os.listdir(REPORT_DIR):
            if file.endswith('.html') and ('report' in file.lower() or 'Report' in file):
                file_path = os.path.join(REPORT_DIR, file)
                reports.append({
                    'filename': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created_time': datetime.fromtimestamp(
                        os.path.getctime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })

        reports.sort(key=lambda x: x['created_time'], reverse=True)
        
        total = len(reports)
        total_pages = (total + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        paginated_reports = reports[start:end]
        
        logger.info(f"找到 {total} 个测试报告，第 {page}/{total_pages} 页")
        return jsonify({
            'success': True, 
            'data': paginated_reports,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        })
    except Exception as e:
        logger.error(f"获取报告列表失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/view_report')
def view_report():
    report_path = request.args.get('path', '')
    filename = request.args.get('file', '')

    if not report_path and filename:
        report_path = os.path.join(REPORT_DIR, filename)
    
    logger.info(f"查看报告：{report_path}")
    
    if not report_path or not os.path.exists(report_path):
        logger.error(f"报告文件不存在：{report_path}")
        return jsonify({'success': False, 'message': '报告文件不存在'}), 404

    return send_file(report_path, mimetype='text/html')


@app.route('/reports')
def reports_page():
    """报告列表页面"""
    logger.info("访问报告列表页面")
    return render_template('reports.html')


@app.route('/api/screenshots')
def list_screenshots():
    """获取截图列表"""
    screenshot_dir = os.path.join(REPORT_DIR, 'screenshots')
    logger.info(f"获取截图列表，目录：{screenshot_dir}")
    
    if not os.path.exists(screenshot_dir):
        logger.warning(f"截图目录不存在：{screenshot_dir}")
        return jsonify({'success': False, 'message': f'截图目录不存在：{screenshot_dir}'})
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    screenshots = []
    try:
        for file in os.listdir(screenshot_dir):
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                file_path = os.path.join(screenshot_dir, file)
                screenshots.append({
                    'filename': file,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'created_time': datetime.fromtimestamp(
                        os.path.getctime(file_path)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                })

        screenshots.sort(key=lambda x: x['created_time'], reverse=True)
        
        total = len(screenshots)
        total_pages = (total + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        paginated_screenshots = screenshots[start:end]
        
        logger.info(f"找到 {total} 个截图，第 {page}/{total_pages} 页")
        return jsonify({
            'success': True, 
            'data': paginated_screenshots,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        })
    except Exception as e:
        logger.error(f"获取截图列表失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/view_screenshot')
def view_screenshot():
    """查看单个截图"""
    filename = request.args.get('file', '')
    
    if not filename:
        logger.error("查看截图失败：未提供文件名")
        return jsonify({'success': False, 'message': '未提供文件名'}), 400
    
    screenshot_path = os.path.join(REPORT_DIR, 'screenshots', filename)
    logger.info(f"查看截图：{screenshot_path}")
    
    if not os.path.exists(screenshot_path):
        logger.error(f"截图文件不存在：{screenshot_path}")
        return jsonify({'success': False, 'message': '截图文件不存在'}), 404

    return send_file(screenshot_path, mimetype='image/png')


@app.route('/screenshots')
def screenshots_page():
    """截图列表页面"""
    logger.info("访问截图列表页面")
    return render_template('screenshots.html')


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 自动化测试平台启动")
    logger.info(f"📁 报告目录：{REPORT_DIR}")
    logger.info("📱 访问地址：http://localhost:5000")
    logger.info("=" * 60)
    print("=" * 60)
    print("🚀 自动化测试平台启动")
    print(f"📁 报告目录：{REPORT_DIR}")
    print("📱 访问地址：http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, host='0.0.0.0',use_reloader=False)
