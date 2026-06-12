import os
import json
import threading
from flask import Blueprint, jsonify, request, render_template, send_file
from werkzeug.utils import secure_filename
from web_ui.conf import logger
from page.llmClient import LLMClient
from page.llmChatManager import LLMChatManager
from page.llmCaseGenerator import LLMCaseGenerator
from page.llmXlsxManager import LLMXlsxManager
from page.llmTools import TOOLS_SPEC, ANALYSIS_TOOLS_SPEC, get_tool_executor, api_manager, ui_manager
from page.api_page import ApiTester
from page.uiTestExecutor import UITestExecutor
from page.apiTestReusltManager import ApiTestResultManager
from page.uiTestResultManager import UITestResultManager
from datetime import datetime

llm_bp = Blueprint('llm', __name__)

chat_manager = LLMChatManager()
case_generator = LLMCaseGenerator()
xlsx_manager = LLMXlsxManager()
api_result_manager = ApiTestResultManager()
ui_result_manager = UITestResultManager()

# 增强对话系统提示词（支持工具调用分析）
ENHANCED_CHAT_SYSTEM_PROMPT = """你是一名专业的软件测试工程师助手，擅长测试用例设计、需求分析、自动化测试和测试质量分析。请用中文回答。

你可以使用以下工具来帮助分析现有的测试用例和执行结果：
1. get_api_test_cases - 获取所有API测试用例
2. get_ui_test_cases - 获取所有UI测试用例
3. get_api_test_results - 获取最近的API测试结果
4. get_ui_test_results - 获取最近的UI测试结果
5. get_test_result_detail - 获取指定任务的详细执行结果

当用户询问关于现有测试用例分析、测试结果回顾、改进建议等问题时，请主动使用这些工具来获取数据进行分析。

注意：
- 调用工具后，系统会返回数据结果，请基于返回的数据进行分析
- 分析时要考虑用例的完整性、执行通过率、覆盖场景等
- 给出具体、可操作的建议"""

# 一键分析系统提示词
ANALYSIS_SYSTEM_PROMPT = """你是一名资深的测试架构师，擅长分析测试用例质量、测试执行情况和测试覆盖率。
请根据提供的测试用例数据和测试执行结果，进行全面的质量分析。

请输出严格的 JSON 格式结果，不要输出任何 JSON 以外的内容。

输出 JSON 结构如下：
{
    "overview": {
        "api_case_count": 0,
        "ui_case_count": 0,
        "api_execution_count": 0,
        "ui_execution_count": 0,
        "api_pass_rate": "0%",
        "ui_pass_rate": "0%"
    },
    "case_quality_analysis": "用例质量分析（Markdown格式）",
    "execution_analysis": "执行结果分析（Markdown格式）",
    "coverage_analysis": "覆盖情况分析（Markdown格式）",
    "suggestions": [
        {
            "category": "用例改进/场景补充/执行优化/其他",
            "priority": "高/中/低",
            "content": "具体建议内容"
        }
    ],
    "summary": "总结（Markdown格式）"
}
"""

ALLOWED_EXTENSIONS = {'txt', 'md', 'docx', 'doc', 'json', 'yaml', 'yml'}


def _get_file_extension(filename):
    """从文件名提取扩展名（不含点），支持中文文件名"""
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def _allowed_file(filename):
    return _get_file_extension(filename) in ALLOWED_EXTENSIONS


def _build_save_name(original_filename):
    """
    生成安全的保存文件名，保留扩展名
    secure_filename 会 stripping 中文字符，因此扩展名单独从原始文件名提取
    """
    ext = _get_file_extension(original_filename)
    if ext not in ALLOWED_EXTENSIONS:
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name_part = secure_filename(os.path.splitext(original_filename)[0])
    if not name_part:
        name_part = 'upload'
    return f"{timestamp}_{name_part}.{ext}"


# ==================== 页面路由 ====================

@llm_bp.route('/llm')
def llm_page():
    """LLM 智能测试助手页面"""
    return render_template('llm.html')


# ==================== 对话 API ====================

@llm_bp.route('/api/llm/config', methods=['GET'])
def get_llm_config():
    """获取 LLM 配置状态"""
    try:
        client = LLMClient()
        return jsonify({
            'success': True,
            'data': {
                'configured': client.is_configured(),
                'model': client.model,
                'base_url': client.base_url
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@llm_bp.route('/api/llm/sessions', methods=['GET'])
def list_sessions():
    """获取对话会话列表"""
    try:
        sessions = chat_manager.list_sessions()
        return jsonify({'success': True, 'data': sessions})
    except Exception as e:
        logger.error(f"获取对话列表失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@llm_bp.route('/api/llm/sessions', methods=['POST'])
def create_session():
    """创建新对话会话"""
    try:
        data = request.json or {}
        session = chat_manager.create_session(data.get('title'))
        return jsonify({'success': True, 'data': session}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@llm_bp.route('/api/llm/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """获取对话会话详情"""
    session = chat_manager.get_session(session_id)
    if session:
        return jsonify({'success': True, 'data': session})
    return jsonify({'success': False, 'message': '会话不存在'}), 404


@llm_bp.route('/api/llm/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除对话会话"""
    if chat_manager.delete_session(session_id):
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '会话不存在'}), 404


@llm_bp.route('/api/llm/chat', methods=['POST'])
def chat():
    """与大模型对话"""
    try:
        data = request.json
        session_id = data.get('session_id')
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'success': False, 'message': '消息不能为空'}), 400

        if not session_id:
            session = chat_manager.create_session()
            session_id = session['session_id']

        chat_manager.add_message(session_id, 'user', message)

        session = chat_manager.get_session(session_id)
        llm_messages = [
            {'role': 'system', 'content': '你是一名专业的软件测试工程师助手，擅长测试用例设计、需求分析和自动化测试。请用中文回答。'}
        ]
        for msg in session['messages']:
            llm_messages.append({'role': msg['role'], 'content': msg['content']})

        client = LLMClient()
        reply = client.chat(llm_messages)
        chat_manager.add_message(session_id, 'assistant', reply)

        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'reply': reply
            }
        })
    except Exception as e:
        logger.error(f"对话失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 增强对话API（支持工具调用分析）====================

@llm_bp.route('/api/llm/chat_with_tools', methods=['POST'])
def chat_with_tools():
    """与大模型对话（支持Function Calling，可主动获取测试数据进行分析）"""
    try:
        data = request.json
        session_id = data.get('session_id')
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'success': False, 'message': '消息不能为空'}), 400

        if not session_id:
            session = chat_manager.create_session()
            session_id = session['session_id']

        chat_manager.add_message(session_id, 'user', message)

        session = chat_manager.get_session(session_id)
        llm_messages = [
            {'role': 'system', 'content': ENHANCED_CHAT_SYSTEM_PROMPT}
        ]
        for msg in session['messages']:
            role = msg['role']
            content = msg['content']
            # 跳过可能带tool_calls的消息（简化为纯文本消息）
            if role in ('user', 'assistant'):
                llm_messages.append({'role': role, 'content': content})

        client = LLMClient()

        # 第一轮：调用LLM可能返回工具调用
        result = client.chat_with_tools(llm_messages, tools=ANALYSIS_TOOLS_SPEC)

        tool_call_results = []

        # 如果AI决定调用工具
        if result['tool_calls']:
            logger.info(f"AI 请求调用 {len(result['tool_calls'])} 个工具进行分析")

            # 将AI的tool_calls消息加入历史
            assistant_msg = {
                'role': 'assistant',
                'content': result.get('content'),
                'tool_calls': [
                    {
                        'id': tc['id'],
                        'type': 'function',
                        'function': {
                            'name': tc['function']['name'],
                            'arguments': tc['function']['arguments']
                        }
                    }
                    for tc in result['tool_calls']
                ]
            }
            llm_messages.append(assistant_msg)

            for tool_call in result['tool_calls']:
                func_name = tool_call['function']['name']
                args = json.loads(tool_call['function']['arguments'])

                logger.info(f"执行工具调用: {func_name}")

                executor = get_tool_executor(func_name)
                if executor:
                    exec_result = executor(args)
                    tool_call_results.append({
                        'tool': func_name,
                        'success': exec_result.get('success', False),
                        'result': exec_result
                    })
                    # 将工具执行结果加入消息历史
                    llm_messages.append({
                        'role': 'tool',
                        'tool_call_id': tool_call['id'],
                        'content': json.dumps(exec_result, ensure_ascii=False)
                    })
                else:
                    logger.warning(f"未找到工具执行器: {func_name}")
                    tool_call_results.append({
                        'tool': func_name,
                        'success': False,
                        'error': f'未知工具: {func_name}'
                    })

            # 第二轮：将工具结果传给LLM，获取最终分析回复
            logger.info("将工具结果传回LLM，获取最终分析回复...")
            final_content = client.chat(llm_messages)
            chat_manager.add_message(session_id, 'assistant', final_content)

            return jsonify({
                'success': True,
                'data': {
                    'session_id': session_id,
                    'reply': final_content,
                    'tool_calls': tool_call_results
                }
            })
        else:
            # 没有工具调用，直接返回文本回复
            reply = result.get('content', '')
            chat_manager.add_message(session_id, 'assistant', reply)

            return jsonify({
                'success': True,
                'data': {
                    'session_id': session_id,
                    'reply': reply,
                    'tool_calls': []
                }
            })

    except Exception as e:
        logger.error(f"对话失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 需求文档上传 ====================

@llm_bp.route('/api/llm/upload', methods=['POST'])
def upload_requirement():
    """上传需求文档"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'message': '文件名不能为空'}), 400

        if not _allowed_file(file.filename):
            return jsonify({'success': False, 'message': f'不支持的文件格式，仅支持: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        save_name = _build_save_name(file.filename)
        if not save_name:
            return jsonify({'success': False, 'message': '无法识别文件格式，请确保文件有正确的扩展名'}), 400

        filepath = os.path.join(xlsx_manager.get_upload_dir(), save_name)
        file.save(filepath)

        content = case_generator.read_document(filepath)
        logger.info(f"需求文档已上传: {save_name}, 内容长度: {len(content)}")

        return jsonify({
            'success': True,
            'data': {
                'filename': save_name,
                'original_name': file.filename,
                'content_preview': content[:500] + ('...' if len(content) > 500 else ''),
                'content_length': len(content)
            }
        })
    except Exception as e:
        logger.error(f"上传需求文档失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 用例生成 ====================

@llm_bp.route('/api/llm/generate', methods=['POST'])
def generate_cases():
    """根据需求文本或已上传文件生成测试用例"""
    try:
        data = request.json or {}
        requirement_text = data.get('requirement_text', '').strip()
        uploaded_file = data.get('uploaded_file', '')
        extra_prompt = data.get('extra_prompt', '')

        if uploaded_file:
            filepath = os.path.join(xlsx_manager.get_upload_dir(), os.path.basename(uploaded_file))
            if not os.path.exists(filepath):
                return jsonify({'success': False, 'message': '上传的文件不存在'}), 404
            result, xlsx_filename = case_generator.generate_from_file(filepath, extra_prompt)
        elif requirement_text:
            result, xlsx_filename = case_generator.generate_from_text(requirement_text, extra_prompt)
        else:
            return jsonify({'success': False, 'message': '请提供需求文本或上传需求文档'}), 400

        return jsonify({
            'success': True,
            'data': {
                'xlsx_filename': xlsx_filename,
                'requirements_analysis': result.get('requirements_analysis', ''),
                'api_cases': result.get('api_cases', []),
                'ui_cases': result.get('ui_cases', []),
                'api_count': len(result.get('api_cases', [])),
                'ui_count': len(result.get('ui_cases', []))
            }
        })
    except Exception as e:
        logger.error(f"生成测试用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== XLSX 文件管理 ====================

@llm_bp.route('/api/llm/files', methods=['GET'])
def list_generated_files():
    """列出所有生成的 xlsx 文件"""
    try:
        files = xlsx_manager.list_files()
        return jsonify({'success': True, 'data': files, 'total': len(files)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@llm_bp.route('/api/llm/files/<filename>', methods=['GET'])
def download_file(filename):
    """下载 xlsx 文件"""
    filepath = xlsx_manager.get_filepath(filename)
    if filepath:
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({'success': False, 'message': '文件不存在'}), 404


@llm_bp.route('/api/llm/files/<filename>/preview', methods=['GET'])
def preview_file(filename):
    """预览 xlsx 文件中的测试用例"""
    try:
        data = xlsx_manager.read_cases_from_xlsx(filename)
        if not data:
            return jsonify({'success': False, 'message': '文件不存在'}), 404
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 用例导入与执行 ====================

@llm_bp.route('/api/llm/import', methods=['POST'])
def import_cases():
    """将生成的用例导入测试平台"""
    try:
        data = request.json or {}
        xlsx_filename = data.get('xlsx_filename', '')
        cases_data = data.get('cases_data')

        if xlsx_filename:
            import_result = case_generator.import_from_xlsx(xlsx_filename)
        elif cases_data:
            import_result = case_generator.import_to_platform(cases_data)
        else:
            return jsonify({'success': False, 'message': '请提供 xlsx 文件名或用例数据'}), 400

        return jsonify({
            'success': True,
            'data': import_result,
            'message': f'导入成功: 接口用例 {import_result["api_count"]} 个, UI用例 {import_result["ui_count"]} 个'
        })
    except Exception as e:
        logger.error(f"导入用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@llm_bp.route('/api/llm/run_cases', methods=['POST'])
def run_generated_cases():
    """执行生成的测试用例（接口+UI）"""
    try:
        data = request.json or {}
        api_cases = data.get('api_cases', [])
        ui_cases = data.get('ui_cases', [])
        xlsx_filename = data.get('xlsx_filename', '')

        if xlsx_filename and not api_cases and not ui_cases:
            file_data = xlsx_manager.read_cases_from_xlsx(xlsx_filename)
            if file_data:
                api_cases = file_data.get('api_cases', [])
                ui_cases = file_data.get('ui_cases', [])

        if not api_cases and not ui_cases:
            return jsonify({'success': False, 'message': '没有可执行的测试用例'}), 400

        task_id = f"llm_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        results = {'api_results': [], 'ui_results': [], 'task_id': task_id}

        # 执行接口用例
        if api_cases:
            tester = ApiTester()
            try:
                api_results = tester.run_api_tests(api_cases)
                results['api_results'] = api_results
                api_result_manager.save_result(task_id, api_results,
                                               [c.get('name', '') for c in api_cases])
            finally:
                tester.close()

        # 执行 UI 用例
        if ui_cases:
            executor = UITestExecutor()
            for case in ui_cases:
                ui_result = executor.execute_case(case)
                results['ui_results'].append(ui_result)

        api_passed = sum(1 for r in results['api_results'] if r.get('passed'))
        api_failed = len(results['api_results']) - api_passed
        ui_passed = sum(1 for r in results['ui_results'] if r.get('passed'))
        ui_failed = len(results['ui_results']) - ui_passed

        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'summary': {
                    'api_total': len(results['api_results']),
                    'api_passed': api_passed,
                    'api_failed': api_failed,
                    'ui_total': len(results['ui_results']),
                    'ui_passed': ui_passed,
                    'ui_failed': ui_failed
                },
                'api_results': results['api_results'],
                'ui_results': results['ui_results']
            }
        })
    except Exception as e:
        logger.error(f"执行用例失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== AI 智能生成（Function Calling）====================

@llm_bp.route('/api/llm/smart_generate', methods=['POST'])
def smart_generate():
    """
    AI 智能生成测试用例（支持 Function Calling）
    AI 可以根据需求描述自动决定调用本地方法生成用例
    """
    try:
        data = request.json or {}
        requirement = data.get('requirement', '').strip()
        extra_prompt = data.get('extra_prompt', '')
        
        if not requirement:
            return jsonify({'success': False, 'message': '请提供需求描述'}), 400
        
        # 构建系统提示词
        system_prompt = """你是一名资深的测试工程师，擅长根据需求描述设计测试用例。
        
你可以使用以下工具来帮助生成测试用例：
1. generate_api_test_case - 生成单个接口测试用例
2. generate_ui_test_case - 生成单个UI测试用例
3. batch_generate_api_cases - 批量生成多个接口测试用例
4. batch_generate_ui_cases - 批量生成多个UI测试用例

工作流程：
1. 分析用户需求，理解需要测试的功能
2. 设计合适的测试用例（包括正常场景和异常场景）
3. 调用相应的工具将用例保存到平台
4. 向用户汇报生成的用例情况

注意：
- 优先使用批量工具（batch_generate_*）当有多个用例时
- 确保用例名称清晰、描述准确
- 覆盖主要的测试场景"""
        
        user_message = f"""请根据以下需求描述，设计并生成测试用例：

{requirement}

{extra_prompt}"""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]
        
        # 调用 LLM（带工具）
        client = LLMClient()
        result = client.chat_with_tools(messages, tools=TOOLS_SPEC)
        
        tool_call_results = []
        
        # 如果 AI 决定调用工具
        if result['tool_calls']:
            for tool_call in result['tool_calls']:
                func_name = tool_call['function']['name']
                args = json.loads(tool_call['function']['arguments'])
                
                logger.info(f"执行工具调用: {func_name}")
                
                # 获取并执行对应的工具函数
                executor = get_tool_executor(func_name)
                if executor:
                    exec_result = executor(args)
                    tool_call_results.append({
                        'tool': func_name,
                        'success': exec_result.get('success', False),
                        'result': exec_result
                    })
                else:
                    logger.warning(f"未找到工具执行器: {func_name}")
                    tool_call_results.append({
                        'tool': func_name,
                        'success': False,
                        'error': f'未知工具: {func_name}'
                    })
        
        # 统计结果
        total_tools = len(tool_call_results)
        success_tools = sum(1 for r in tool_call_results if r.get('success'))
        
        response_data = {
            'ai_content': result['content'],  # AI 的文本回复（如果有）
            'tool_calls_count': total_tools,
            'success_count': success_tools,
            'failed_count': total_tools - success_tools,
            'tool_results': tool_call_results
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"AI 智能生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 测试用例分析与建议 ====================

@llm_bp.route('/api/llm/analyze', methods=['POST'])
def analyze_test_cases():
    """
    一键分析系统中的所有测试用例和测试执行结果
    自动收集所有数据并让AI进行全面分析，返回结构化建议
    """
    try:
        logger.info("开始全面分析测试用例和测试结果...")

        # 1. 收集所有测试数据
        api_tests = api_manager.get_all_tests()
        ui_cases = ui_manager.get_all_cases()

        api_results_list, api_results_total = api_result_manager.list_results(page=1, per_page=20)
        ui_results_list, ui_results_total = ui_result_manager.list_results(page=1, per_page=20)

        # 2. 加载最近的详细结果
        latest_api_detail = None
        if api_results_list:
            latest_api_task = api_results_list[0].get('task_id', '')
            if latest_api_task:
                latest_api_detail = api_result_manager.get_result(latest_api_task)

        latest_ui_detail = None
        if ui_results_list:
            latest_ui_task = ui_results_list[0].get('task_id', '')
            if latest_ui_task:
                latest_ui_detail = ui_result_manager.get_result(latest_ui_task)

        # 3. 构建上下文
        context = {
            'api_test_cases': [
                {
                    'name': t.get('name', ''),
                    'description': t.get('description', ''),
                    'method': t.get('request', {}).get('method', ''),
                    'url': t.get('request', {}).get('url', ''),
                    'assert_rules': t.get('assert', {})
                } for t in api_tests
            ],
            'ui_test_cases': [
                {
                    'name': c.get('name', ''),
                    'description': c.get('description', ''),
                    'url': c.get('url', ''),
                    'steps_count': len(c.get('steps', [])),
                    'steps_summary': [s.get('action', '') for s in c.get('steps', [])]
                } for c in ui_cases
            ],
            'api_execution_history': [
                {
                    'task_id': r.get('task_id', ''),
                    'total': r.get('total', 0),
                    'passed': r.get('passed', 0),
                    'failed': r.get('failed', 0),
                    'executed_at': r.get('executed_at', ''),
                    'test_names': r.get('test_names', [])
                } for r in api_results_list
            ],
            'ui_execution_history': [
                {
                    'task_id': r.get('task_id', ''),
                    'total': r.get('total', 0),
                    'passed': r.get('passed', 0),
                    'failed': r.get('failed', 0),
                    'executed_at': r.get('executed_at', ''),
                    'case_names': r.get('case_names', [])
                } for r in ui_results_list
            ],
            'latest_api_detail': latest_api_detail,
            'latest_ui_detail': latest_ui_detail
        }

        context_json = json.dumps(context, ensure_ascii=False, indent=2)
        logger.info(f"分析数据已收集: API用例={len(api_tests)}, UI用例={len(ui_cases)}, "
                    f"API执行记录={api_results_total}, UI执行记录={ui_results_total}")

        # 4. 调用LLM进行分析
        user_prompt = f"""请对以下测试用例和测试执行数据进行全面分析，给出详细的改进建议。

分析数据：
{context_json}"""

        messages = [
            {'role': 'system', 'content': ANALYSIS_SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt}
        ]

        client = LLMClient()
        response = client.chat(messages)

        # 5. 解析JSON结果
        result = LLMClient.extract_json(response)

        logger.info("分析完成")

        # 6. 将原始用例数据也一并返回，方便前端展示
        api_case_list = [
            {
                'name': t.get('name', ''),
                'description': t.get('description', ''),
                'method': t.get('request', {}).get('method', ''),
                'url': t.get('request', {}).get('url', ''),
                'id': t.get('id', ''),
                'created_at': t.get('created_at', ''),
                'updated_at': t.get('updated_at', '')
            } for t in api_tests
        ]
        ui_case_list = [
            {
                'name': c.get('name', ''),
                'description': c.get('description', ''),
                'url': c.get('url', ''),
                'steps_count': len(c.get('steps', [])),
                'id': c.get('id', ''),
                'created_at': c.get('created_at', ''),
                'updated_at': c.get('updated_at', '')
            } for c in ui_cases
        ]

        return jsonify({
            'success': True,
            'data': {
                'analysis': result,
                'api_cases': api_case_list,
                'ui_cases': ui_case_list
            }
        })

    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
