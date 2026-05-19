from flask import Blueprint, jsonify, request
from web_ui.conf import logger
from page.api_page import ApiTester
from page.apiTestManager import ApiTestManager
from page.apiTestReusltManager import ApiTestResultManager
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

test_manager = ApiTestManager()
result_manager = ApiTestResultManager()


@api_bp.route('/api_tests', methods=['GET'])
def get_api_tests():
    """获取所有接口测试用例"""
    try:
        tests = test_manager.get_all_tests()
        return jsonify({
            'success': True,
            'data': tests,
            'total': len(tests)
        })
    except Exception as e:
        logger.error(f"获取接口测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/api_tests/<test_id>', methods=['GET'])
def get_api_test(test_id):
    """获取单个接口测试用例"""
    try:
        test = test_manager.get_test_by_id(test_id)
        if test:
            return jsonify({'success': True, 'data': test})
        else:
            return jsonify({'success': False, 'message': '测试用例不存在'}), 404
    except Exception as e:
        logger.error(f"获取接口测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/api_tests', methods=['POST'])
def create_api_test():
    """创建接口测试用例"""
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'success': False, 'message': '测试名称不能为空'}), 400

        test = test_manager.add_test(data)
        logger.info(f"创建接口测试用例: {test['name']}")
        return jsonify({'success': True, 'data': test}), 201
    except Exception as e:
        logger.error(f"创建接口测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/api_tests/<test_id>', methods=['PUT'])
def update_api_test(test_id):
    """更新接口测试用例"""
    try:
        data = request.json
        test = test_manager.update_test(test_id, data)

        if test:
            logger.info(f"更新接口测试用例: {test['name']}")
            return jsonify({'success': True, 'data': test})
        else:
            return jsonify({'success': False, 'message': '测试用例不存在'}), 404
    except Exception as e:
        logger.error(f"更新接口测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/api_tests/<test_id>', methods=['DELETE'])
def delete_api_test(test_id):
    """删除接口测试用例"""
    try:
        test_manager.delete_test(test_id)
        logger.info(f"删除接口测试用例: {test_id}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除接口测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/api_tests/batch_delete', methods=['POST'])
def batch_delete_api_tests():
    """批量删除接口测试用例"""
    try:
        data = request.json
        test_ids = data.get('test_ids', [])

        if not test_ids:
            return jsonify({'success': False, 'message': '请选择要删除的测试用例'}), 400

        test_manager.batch_delete_tests(test_ids)
        logger.info(f"批量删除接口测试用例: {len(test_ids)}个")
        return jsonify({'success': True, 'message': f'成功删除{len(test_ids)}个测试用例'})
    except Exception as e:
        logger.error(f"批量删除接口测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/run_single_test', methods=['POST'])
def run_single_test():
    """执行单个接口测试"""
    try:
        data = request.json
        test_id = data.get('test_id')

        if not test_id:
            return jsonify({'success': False, 'message': '测试用例ID不能为空'}), 400

        test = test_manager.get_test_by_id(test_id)
        if not test:
            return jsonify({'success': False, 'message': '测试用例不存在'}), 404

        tester = ApiTester()
        try:
            result = tester.run_api_test(test)

            task_id = f"single_{test_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            result_manager.save_result(task_id, [result])

            return jsonify({
                'success': True,
                'data': {
                    'task_id': task_id,
                    'result': result
                }
            })
        finally:
            tester.close()
    except Exception as e:
        logger.error(f"执行接口测试失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/run_batch_tests', methods=['POST'])
def run_batch_tests():
    """批量执行接口测试"""
    try:
        data = request.json
        test_ids = data.get('test_ids', [])

        if not test_ids:
            all_tests = test_manager.get_all_tests()
            test_ids = [test['id'] for test in all_tests]

        tests = []
        for test_id in test_ids:
            test = test_manager.get_test_by_id(test_id)
            if test:
                tests.append(test)

        if not tests:
            return jsonify({'success': False, 'message': '没有找到有效的测试用例'}), 404

        task_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        tester = ApiTester()
        try:
            results = tester.run_api_tests(tests)

            summary = result_manager.save_result(task_id, results)

            passed_count = summary['passed']
            failed_count = summary['failed']

            logger.info(f"批量接口测试完成: 总计{len(results)}, 通过{passed_count}, 失败{failed_count}")

            return jsonify({
                'success': True,
                'data': {
                    'task_id': task_id,
                    'summary': summary
                }
            })
        finally:
            tester.close()
    except Exception as e:
        logger.error(f"批量执行接口测试失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/test_results', methods=['GET'])
def get_test_results():
    """获取测试结果列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        results, total = result_manager.list_results(page, per_page)

        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify({
            'success': True,
            'data': results,
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
        logger.error(f"获取测试结果列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/test_results/<task_id>', methods=['GET'])
def get_test_result(task_id):
    """获取单个测试结果详情"""
    try:
        result = result_manager.get_result(task_id)

        if result:
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'message': '测试结果不存在'}), 404
    except Exception as e:
        logger.error(f"获取测试结果失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/test_results/<task_id>', methods=['DELETE'])
def delete_test_result(task_id):
    """删除测试结果"""
    try:
        result_manager.delete_result(task_id)
        logger.info(f"删除测试结果: {task_id}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除测试结果失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500