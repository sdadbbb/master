import os
import threading
from flask import Blueprint, jsonify, request, render_template, send_file
from werkzeug.utils import secure_filename
from web_ui.conf import logger
from page.llmClient import LLMClient
from page.llmChatManager import LLMChatManager
from page.llmCaseGenerator import LLMCaseGenerator
from page.llmXlsxManager import LLMXlsxManager
from page.api_page import ApiTester
from page.uiTestExecutor import UITestExecutor
from page.apiTestReusltManager import ApiTestResultManager
from datetime import datetime

llm_bp = Blueprint('llm', __name__)

chat_manager = LLMChatManager()
case_generator = LLMCaseGenerator()
xlsx_manager = LLMXlsxManager()
api_result_manager = ApiTestResultManager()

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
