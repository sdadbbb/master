import threading

from flask import Blueprint, jsonify, request, render_template
from web_ui.conf import logger, get_running_tasks
from page.uiTestCaseManager import UITestCaseManager
from page.uiTestExecutor import UITestExecutor
from page.uiTestResultManager import UITestResultManager
from datetime import datetime
from web_ui.task import create_project_zip


ui_test_bp = Blueprint('ui_test', __name__, url_prefix='/api')

ui_case_manager = UITestCaseManager()
ui_result_manager = UITestResultManager()


@ui_test_bp.route('/ui_test_editor')
def ui_test_editor_page():
    """UI测试编辑器页面"""
    return render_template('uitest.html')


@ui_test_bp.route('/ui_test_cases_list')
def ui_test_cases_list_page():
    """UI测试用例列表页面"""
    return render_template('ui_test_cases_list.html')


@ui_test_bp.route('/ui_test_cases', methods=['GET'])
def get_ui_test_cases():
    """获取所有UI测试用例"""
    try:
        cases = ui_case_manager.get_all_cases()
        return jsonify({
            'success': True,
            'data': cases,
            'total': len(cases)
        })
    except Exception as e:
        logger.error(f"获取UI测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_cases/<case_id>', methods=['GET'])
def get_ui_test_case(case_id):
    """获取单个UI测试用例"""
    try:
        case = ui_case_manager.get_case_by_id(case_id)
        if case:
            return jsonify({'success': True, 'data': case})
        else:
            return jsonify({'success': False, 'message': '测试用例不存在'}), 404
    except Exception as e:
        logger.error(f"获取UI测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_cases', methods=['POST'])
def create_ui_test_case():
    """创建UI测试用例"""
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'success': False, 'message': '测试名称不能为空'}), 400

        case = ui_case_manager.add_case(data)
        logger.info(f"创建UI测试用例: {case['name']}")
        return jsonify({'success': True, 'data': case}), 201
    except Exception as e:
        logger.error(f"创建UI测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_cases/<case_id>', methods=['PUT'])
def update_ui_test_case(case_id):
    """更新UI测试用例"""
    try:
        data = request.json
        case = ui_case_manager.update_case(case_id, data)

        if case:
            logger.info(f"更新UI测试用例: {case['name']}")
            return jsonify({'success': True, 'data': case})
        else:
            return jsonify({'success': False, 'message': '测试用例不存在'}), 404
    except Exception as e:
        logger.error(f"更新UI测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_cases/<case_id>', methods=['DELETE'])
def delete_ui_test_case(case_id):
    """删除UI测试用例"""
    try:
        ui_case_manager.delete_case(case_id)
        logger.info(f"删除UI测试用例: {case_id}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除UI测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_cases/batch_delete', methods=['POST'])
def batch_delete_ui_test_cases():
    """批量删除UI测试用例"""
    try:
        data = request.json
        case_ids = data.get('case_ids', [])

        if not case_ids:
            return jsonify({'success': False, 'message': '请选择要删除的测试用例'}), 400

        ui_case_manager.batch_delete_cases(case_ids)
        logger.info(f"批量删除UI测试用例: {len(case_ids)}个")
        return jsonify({'success': True, 'message': f'成功删除{len(case_ids)}个测试用例'})
    except Exception as e:
        logger.error(f"批量删除UI测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/run_ui_test_case', methods=['POST'])
def run_ui_test_case():
    """下发 UI 测试任务（异步模式）"""
    try:
        data = request.json
        case_id = data.get('case_id')

        if not case_id:
            return jsonify({'success': False, 'message': '测试用例ID不能为空'}), 400

        case = ui_case_manager.get_case_by_id(case_id)
        if not case:
            return jsonify({'success': False, 'message': '测试用例不存在'}), 404

        task_id = f"ui_{case_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"收到 UI 测试执行请求：{case['name']}，任务 ID: {task_id}")

        zip_path = create_project_zip(task_id)

        running_tasks = get_running_tasks()
        running_tasks[task_id] = {
            'status': 'waiting_local',
            'success': None,
            'output': 'UI 测试任务已发布，等待本地代理领取...',
            'report_path': None,
            'case_id': case_id,
            'case_name': case['name'],
            'test_name': case_id,
            'type': 'ui_test'
        }
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务已发布'
        })
    except Exception as e:
        logger.error(f"下发 UI 测试任务失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


def _run_batch_ui_tests_in_background(task_id, cases, case_names):
    """后台线程执行批量 UI 测试"""
    executor = UITestExecutor()
    running_tasks = get_running_tasks()

    def update_progress(current, total, case_name):
        running_tasks[task_id] = {
            'status': 'executing',
            'success': None,
            'output': f'正在执行 ({current}/{total}): {case_name}',
            'report_path': None,
            'type': 'ui_test_batch',
            'case_names': case_names,
            'progress': {'current': current, 'total': total, 'case_name': case_name}
        }

    try:
        results = executor.execute_cases(cases, progress_callback=update_progress)
        summary = ui_result_manager.save_result(task_id, results, case_names)

        passed_count = summary['passed']
        failed_count = summary['failed']

        running_tasks[task_id] = {
            'status': 'completed',
            'success': failed_count == 0,
            'output': f'批量执行完成: 总计{summary["total"]}, 通过{passed_count}, 失败{failed_count}',
            'report_path': None,
            'type': 'ui_test_batch',
            'case_names': case_names,
            'summary': summary,
            'progress': {'current': summary['total'], 'total': summary['total']}
        }
        logger.info(f"批量UI测试完成: 任务 {task_id}, 通过 {passed_count}, 失败 {failed_count}")
    except Exception as e:
        logger.error(f"批量UI测试异常: {str(e)}")
        running_tasks[task_id] = {
            'status': 'error',
            'success': False,
            'output': f'批量执行异常: {str(e)}',
            'report_path': None,
            'type': 'ui_test_batch',
            'case_names': case_names
        }


@ui_test_bp.route('/run_batch_ui_test_cases', methods=['POST'])
def run_batch_ui_test_cases():
    """批量执行 UI 测试用例（后台异步执行）"""
    try:
        data = request.json
        case_ids = data.get('case_ids', [])

        if not case_ids:
            return jsonify({'success': False, 'message': '请选择要执行的测试用例'}), 400

        cases = []
        case_names = []
        for case_id in case_ids:
            case = ui_case_manager.get_case_by_id(case_id)
            if case:
                cases.append(case)
                case_names.append(case.get('name', case_id))

        if not cases:
            return jsonify({'success': False, 'message': '没有找到有效的测试用例'}), 404

        task_id = f"ui_batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        logger.info(f"收到批量 UI 测试请求: {len(cases)} 个用例, 任务 ID: {task_id}")

        running_tasks = get_running_tasks()
        running_tasks[task_id] = {
            'status': 'executing',
            'success': None,
            'output': f'准备执行 {len(cases)} 个用例...',
            'report_path': None,
            'type': 'ui_test_batch',
            'case_ids': case_ids,
            'case_names': case_names,
            'progress': {'current': 0, 'total': len(cases)}
        }

        thread = threading.Thread(
            target=_run_batch_ui_tests_in_background,
            args=(task_id, cases, case_names),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'已启动批量执行，共 {len(cases)} 个用例'
        })
    except Exception as e:
        logger.error(f"批量执行 UI 测试失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_results', methods=['GET'])
def get_ui_test_results():
    """获取 UI 批量测试结果列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        results, total = ui_result_manager.list_results(page, per_page)
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
        logger.error(f"获取 UI 测试结果列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_results/<task_id>', methods=['GET'])
def get_ui_test_result(task_id):
    """获取单个 UI 批量测试结果详情"""
    try:
        result = ui_result_manager.get_result(task_id)

        if result:
            return jsonify({'success': True, 'data': result})
        else:
            return jsonify({'success': False, 'message': '测试结果不存在'}), 404
    except Exception as e:
        logger.error(f"获取 UI 测试结果失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/ui_test_results/<task_id>', methods=['DELETE'])
def delete_ui_test_result(task_id):
    """删除 UI 测试结果"""
    try:
        ui_result_manager.delete_result(task_id)
        logger.info(f"删除 UI 测试结果: {task_id}")
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除 UI 测试结果失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@ui_test_bp.route('/available_actions', methods=['GET'])
def get_available_actions():
    """获取可用的操作方法列表 - 基于base_page的所有方法"""
    actions = [
        {
            'action': 'go_url',
            'name': '访问URL',
            'description': '打开指定的网页地址',
            'icon': '🌐',
            'category': '导航',
            'params': [
                {'key': 'url', 'label': 'URL地址', 'type': 'string', 'required': True, 'placeholder': 'https://example.com'}
            ]
        },
        {
            'action': 'click_element',
            'name': '点击元素',
            'description': '通过定位器点击页面元素',
            'icon': '👆',
            'category': '操作',
            'params': [
                {'key': 'locator_type', 'label': '定位方式', 'type': 'select', 'required': True, 'default': 'xpath', 
                 'options': ['xpath', 'id', 'css', 'class', 'name', 'tag', 'link_text', 'partial_link_text']},
                {'key': 'locator_value', 'label': '定位器值', 'type': 'string', 'required': True, 'placeholder': '//button[@id="submit"]'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'input_element',
            'name': '输入文本',
            'description': '在输入框中输入文本',
            'icon': '⌨️',
            'category': '操作',
            'params': [
                {'key': 'locator_type', 'label': '定位方式', 'type': 'select', 'required': True, 'default': 'xpath',
                 'options': ['xpath', 'id', 'css', 'class', 'name']},
                {'key': 'locator_value', 'label': '定位器值', 'type': 'string', 'required': True, 'placeholder': '//input[@name="username"]'},
                {'key': 'text', 'label': '输入文本', 'type': 'string', 'required': True, 'placeholder': '支持${variable}变量'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'input_by_placeholder_only',
            'name': '根据提示内容输入',
            'description': '仅根据提示内筒查找输入框并输入',
            'icon': '✏️',
            'category': '操作',
            'params': [
                {'key': 'placeholder', 'label': '输入框提示词', 'type': 'string', 'required': True, 'placeholder': '请输入用户名'},
                {'key': 'text', 'label': '输入文本', 'type': 'string', 'required': True, 'placeholder': '支持${variable}变量'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'input_by_placeholder',
            'name': '弹窗输入',
            'description': '在弹窗的输入框中输入文本',
            'icon': '💬',
            'category': '操作',
            'params': [
                {'key': 'aria_label', 'label': '弹窗标题', 'type': 'string', 'required': True, 'placeholder': '新增用户'},
                {'key': 'placeholder', 'label': '输入框提示词', 'type': 'string', 'required': True, 'placeholder': '请输入用户名'},
                {'key': 'text', 'label': '输入文本', 'type': 'string', 'required': True, 'placeholder': '支持${variable}变量'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'get_element_text',
            'name': '提取文本',
            'description': '获取元素文本并存储到变量',
            'icon': '📋',
            'category': '变量',
            'params': [
                {'key': 'locator_type', 'label': '定位方式', 'type': 'select', 'required': True, 'default': 'xpath',
                 'options': ['xpath', 'id', 'css', 'class', 'name']},
                {'key': 'locator_value', 'label': '定位器值', 'type': 'string', 'required': True},
                {'key': 'var_name', 'label': '变量名', 'type': 'string', 'required': True, 'placeholder': 'my_variable'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'click_button_by_text',
            'name': '点击按钮',
            'description': '通过按钮文本点击按钮',
            'icon': '🔘',
            'category': '操作',
            'params': [
                {'key': 'button_text', 'label': '按钮文本', 'type': 'string', 'required': True, 'placeholder': '确定'},
                {'key': 'aria_label', 'label': '弹窗标题(可选)', 'type': 'string', 'required': False, 'placeholder': '确认对话框'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'click_contains_text',
            'name': '点击包含文本',
            'description': '点击包含指定文本的元素',
            'icon': '🎯',
            'category': '操作',
            'params': [
                {'key': 'text', 'label': '文本内容', 'type': 'string', 'required': True, 'placeholder': '提交'},
                {'key': 'tag_name', 'label': '标签类型', 'type': 'string', 'required': False, 'default': '*', 'placeholder': '* 或 button, div等'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'find_element_by_text',
            'name': '查找元素(精确)',
            'description': '查找精确匹配文本的元素',
            'icon': '🔍',
            'category': '验证',
            'params': [
                {'key': 'text', 'label': '文本内容', 'type': 'string', 'required': True},
                {'key': 'tag_name', 'label': '标签类型', 'type': 'string', 'required': False, 'default': '*'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'find_contains_text_element',
            'name': '查找元素(包含)',
            'description': '查找包含文本的元素',
            'icon': '🔎',
            'category': '验证',
            'params': [
                {'key': 'text', 'label': '文本内容', 'type': 'string', 'required': True},
                {'key': 'tag_name', 'label': '标签类型', 'type': 'string', 'required': False, 'default': '*'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'find_elements_by_text',
            'name': '查找多个元素',
            'description': '查找所有匹配文本的元素',
            'icon': '🔎🔎',
            'category': '验证',
            'params': [
                {'key': 'text', 'label': '文本内容', 'type': 'string', 'required': True},
                {'key': 'tag_name', 'label': '标签类型', 'type': 'string', 'required': False, 'default': '*'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'click_button_by_text_in_form',
            'name': '表单内点击按钮',
            'description': '在指定表单内点击按钮',
            'icon': '📝',
            'category': '操作',
            'params': [
                {'key': 'button_text', 'label': '按钮文本', 'type': 'string', 'required': True},
                {'key': 'form_locator_type', 'label': '表单定位方式', 'type': 'select', 'required': False, 'default': 'xpath',
                 'options': ['xpath', 'id', 'css', 'class']},
                {'key': 'form_locator', 'label': '表单定位器', 'type': 'string', 'required': False, 'placeholder': '//form[@id="myForm"]'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'click_button_element_by_index',
            'name': '点击第N个按钮',
            'description': '点击匹配的第N个按钮元素',
            'icon': '🔢',
            'category': '操作',
            'params': [
                {'key': 'button_text', 'label': '按钮文本', 'type': 'string', 'required': True},
                {'key': 'index', 'label': '索引(从0开始)', 'type': 'number', 'required': True, 'default': 0},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'check_login_result',
            'name': '检查登录结果',
            'description': '检查登录成功或失败',
            'icon': '🔐',
            'category': '验证',
            'params': [
                {'key': 'success_text', 'label': '成功提示文本', 'type': 'string', 'required': True, 'placeholder': '登录成功'},
                {'key': 'error_texts', 'label': '失败提示文本列表', 'type': 'array', 'required': True, 'placeholder': '["用户名错误", "密码错误"]'}
            ]
        },
        {
            'action': 'wait_element',
            'name': '等待元素',
            'description': '等待元素出现',
            'icon': '⏳',
            'category': '等待',
            'params': [
                {'key': 'locator_type', 'label': '定位方式', 'type': 'select', 'required': True, 'default': 'xpath',
                 'options': ['xpath', 'id', 'css', 'class', 'name']},
                {'key': 'locator_value', 'label': '定位器值', 'type': 'string', 'required': True},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        },
        {
            'action': 'wait',
            'name': '固定等待',
            'description': '强制等待指定秒数',
            'icon': '⏰',
            'category': '等待',
            'params': [
                {'key': 'seconds', 'label': '等待秒数', 'type': 'number', 'required': True, 'default': 3}
            ]
        },
        {
            'action': 'assert_text_exists',
            'name': '断言文本存在',
            'description': '验证页面上是否存在指定文本',
            'icon': '✔️',
            'category': '验证',
            'params': [
                {'key': 'text', 'label': '文本内容', 'type': 'string', 'required': True},
                {'key': 'tag_name', 'label': '标签类型', 'type': 'string', 'required': False, 'default': '*'},
                {'key': 'timeout', 'label': '超时时间(秒)', 'type': 'number', 'required': False, 'default': 10}
            ]
        }
    ]
    
    return jsonify({
        'success': True,
        'data': actions
    })
