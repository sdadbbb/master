import os
import json
from datetime import datetime
from util.file_util import FileUtil


class LLMChatManager:
    """大模型对话记录管理器"""

    def __init__(self):
        self.chat_dir = os.path.join(FileUtil.get_project_root(), 'config', 'llm', 'chats')
        self._ensure_chat_dir()

    def _ensure_chat_dir(self):
        """确保对话记录目录存在"""
        os.makedirs(self.chat_dir, exist_ok=True)

    def _get_chat_file(self, session_id):
        return os.path.join(self.chat_dir, f'{session_id}.json')

    def create_session(self, title=None):
        """创建新对话会话"""
        session_id = f"chat_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        session = {
            'session_id': session_id,
            'title': title or f'对话 {datetime.now().strftime("%m-%d %H:%M")}',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'messages': []
        }
        self._save_session(session)
        return session

    def get_session(self, session_id):
        """获取对话会话"""
        filepath = self._get_chat_file(session_id)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def list_sessions(self):
        """列出所有对话会话"""
        self._ensure_chat_dir()
        sessions = []
        if not os.path.isdir(self.chat_dir):
            return sessions

        for fname in os.listdir(self.chat_dir):
            if fname.endswith('.json'):
                with open(os.path.join(self.chat_dir, fname), 'r', encoding='utf-8') as f:
                    session = json.load(f)
                    sessions.append({
                        'session_id': session['session_id'],
                        'title': session.get('title', ''),
                        'created_at': session.get('created_at', ''),
                        'updated_at': session.get('updated_at', ''),
                        'message_count': len(session.get('messages', []))
                    })
        sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return sessions

    def add_message(self, session_id, role, content):
        """添加消息到会话"""
        session = self.get_session(session_id)
        if not session:
            # 会话文件不存在时自动创建，避免前端 session_id 与文件不同步
            session = {
                'session_id': session_id,
                'title': f'对话 {datetime.now().strftime("%m-%d %H:%M")}',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'messages': []
            }

        session['messages'].append({
            'role': role,
            'content': content,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        session['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 首条用户消息作为标题
        if len(session['messages']) == 1 and role == 'user':
            session['title'] = content[:30] + ('...' if len(content) > 30 else '')

        self._save_session(session)
        return session

    def delete_session(self, session_id):
        """删除对话会话"""
        filepath = self._get_chat_file(session_id)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def _save_session(self, session):
        self._ensure_chat_dir()
        filepath = self._get_chat_file(session['session_id'])
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
