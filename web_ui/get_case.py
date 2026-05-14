import os

from flask import Blueprint, jsonify, render_template

from web_ui.conf import logger

case_bp = Blueprint('case', __name__)


@case_bp.route('/')
def index():
    logger.info("访问首页")
    return render_template('index.html')


@case_bp.route('/api/tests')
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
