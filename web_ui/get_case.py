import os

from flask import Blueprint, jsonify, render_template, request

from web_ui.conf import logger

case_bp = Blueprint('case', __name__)


@case_bp.route('/')
def index():
    logger.info("访问首页")
    return render_template('index.html')


@case_bp.route('/api_tests')
def api_tests_page():
    """接口自动化测试页面"""
    logger.info("访问接口自动化测试页面")
    return render_template('apitest.html')


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
        return jsonify({'data': tests})
    except Exception as e:
        logger.exception(f"获取测试用例失败：{str(e)}")
        return jsonify({'data': []})


@case_bp.route('/api/tests/<test_name>', methods=['DELETE'])
def delete_test(test_name):
    """删除pytest测试用例"""
    try:
        import os
        from util.file_util import FileUtil
        
        test_dir = os.path.join(FileUtil.get_project_root(), 'test')
        test_file = os.path.join(test_dir, f'{test_name}.py')
        
        if not os.path.exists(test_file):
            return jsonify({'success': False, 'message': '测试文件不存在'}), 404
        
        os.remove(test_file)
        logger.info(f"删除测试用例: {test_name}")
        
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
