from flask import Flask, render_template, jsonify, request, send_file
import subprocess
import os
import threading
from datetime import datetime

from log.logger import LoggerUtil

# 创建 Flask 应用时指定模板编码
from util.file_util import FileUtil

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False  # 支持中文 JSON

logger = LoggerUtil.get_logger()
# 存储正在运行的测试任务
running_tasks = {}

# 你的 pytest 配置的报告目录（改成你实际配置的位置）
REPORT_DIR = FileUtil.get_report_dir()  # ← 改成你 pytest 生成报告的实际路径

if not os.path.exists(REPORT_DIR):
    logger.warning(f"报告目录不存在，将创建：{REPORT_DIR}")
    os.makedirs(REPORT_DIR, exist_ok=True)
else:
    logger.info(f"报告目录已存在：{REPORT_DIR}")
    logger.info(f"目录中的文件：{os.listdir(REPORT_DIR)}")


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
        logger.error(f"获取测试用例失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/run', methods=['POST'])
def run_test():
    data = request.json
    test_name = data.get('test_name', 'test_ui')
    
    task_id = f"{test_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    logger.info("=" * 60)
    logger.info(f"开始执行测试：{test_name}")
    logger.info(f"任务 ID: {task_id}")
    logger.info(f"报告目录：{REPORT_DIR}")

    os.makedirs(REPORT_DIR, exist_ok=True)

    report_filename = f"{task_id}_report.html"
    report_path = os.path.join(REPORT_DIR, report_filename)

    cmd = [
        'pytest', 
        f'test/{test_name}.py', 
        '-v', 
        '-s',
        '--html', report_path,
        '--self-contained-html'
    ]

    logger.info(f"执行命令：{' '.join(cmd)}")
    logger.info(f"报告路径：{report_path}")

    running_tasks[task_id] = {
        'status': 'running',
        'success': None,
        'output': '',
        'report_path': report_path
    }

    def run_command(task_id):
        logger.info(f"任务 {task_id} 开始执行...")
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # 设置环境变量强制使用 UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__)),
                timeout=300,
                encoding='utf-8',  # ← 关键：指定 UTF-8 编码
                errors='replace',
                startupinfo=startupinfo,
                env=env
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                logger.info(f"✅ 任务 {task_id} 执行成功")
                logger.info(f"输出:\n{output}")

                if os.path.exists(report_path):
                    logger.info(f"报告已生成：{report_path}")
                    logger.info(f"报告大小：{os.path.getsize(report_path)} bytes")
                else:
                    logger.warning(f"报告文件未找到：{report_path}")
                
                running_tasks[task_id] = {
                    'status': 'completed',
                    'success': True,
                    'output': output,
                    'report_path': report_path
                }
            else:
                logger.warning(f"❌ 任务 {task_id} 执行失败")
                logger.warning(f"输出:\n{output}")
                
                running_tasks[task_id] = {
                    'status': 'completed',
                    'success': False,
                    'output': output,
                    'report_path': report_path
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ 任务 {task_id} 执行超时")
            running_tasks[task_id] = {
                'status': 'error',
                'success': False,
                'output': '测试执行超时（超过 5 分钟）',
                'report_path': None
            }
        except UnicodeDecodeError as e:
            logger.error(f"❌ 任务 {task_id} 编码解码错误：{str(e)}")
            running_tasks[task_id] = {
                'status': 'error',
                'success': False,
                'output': f'编码错误：{str(e)}\n请检查测试输出中是否有特殊字符',
                'report_path': None
            }
        except Exception as e:
            logger.error(f"❌ 任务 {task_id} 执行异常：{str(e)}")
            running_tasks[task_id] = {
                'status': 'error',
                'success': False,
                'output': str(e),
                'report_path': None
            }
        finally:
            logger.info(f"任务 {task_id} 执行完毕，状态：{running_tasks[task_id]['status']}")

    thread = threading.Thread(target=run_command, args=(task_id,), daemon=True)
    thread.start()
    
    logger.info(f"任务 {task_id} 已提交到后台执行")
    logger.info("=" * 60)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '测试已开始执行'
    })


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
        
        logger.info(f"找到 {len(reports)} 个测试报告")
        return jsonify({'success': True, 'data': reports})
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
    app.run(debug=True, port=5000, host='0.0.0.0')
