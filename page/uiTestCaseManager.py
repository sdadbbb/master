
import os
import json
from datetime import datetime
from util.file_util import FileUtil


class UITestCaseManager:
    """UI自动化测试用例管理器"""

    def __init__(self):
        self.ui_tests_dir = os.path.join(FileUtil.get_project_root(), 'config', 'ui_tests')
        os.makedirs(self.ui_tests_dir, exist_ok=True)
        self.ui_tests_file = os.path.join(self.ui_tests_dir, 'cases.json')
        self._ensure_file()

    def _ensure_file(self):
        """确保测试用例文件存在"""
        if not os.path.exists(self.ui_tests_file):
            self._save_cases([])

    def _load_cases(self):
        """加载测试用例"""
        try:
            with open(self.ui_tests_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_cases(self, cases):
        """保存测试用例"""
        with open(self.ui_tests_file, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)

    def get_all_cases(self):
        """获取所有测试用例"""
        return self._load_cases()

    def get_case_by_id(self, case_id):
        """根据ID获取测试用例"""
        cases = self._load_cases()
        for case in cases:
            if case.get('id') == case_id:
                return case
        return None

    def add_case(self, case_data):
        """添加测试用例"""
        cases = self._load_cases()

        new_case = {
            'id': f"ui_case_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            'name': case_data.get('name', ''),
            'description': case_data.get('description', ''),
            'url': case_data.get('url', ''),
            'steps': case_data.get('steps', []),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        cases.append(new_case)
        self._save_cases(cases)
        return new_case

    def update_case(self, case_id, case_data):
        """更新测试用例"""
        cases = self._load_cases()

        for i, case in enumerate(cases):
            if case.get('id') == case_id:
                cases[i]['name'] = case_data.get('name', case['name'])
                cases[i]['description'] = case_data.get('description', case['description'])
                cases[i]['url'] = case_data.get('url', case['url'])
                cases[i]['steps'] = case_data.get('steps', case['steps'])
                cases[i]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_cases(cases)
                return cases[i]

        return None

    def delete_case(self, case_id):
        """删除测试用例"""
        cases = self._load_cases()
        cases = [case for case in cases if case.get('id') != case_id]
        self._save_cases(cases)
        return True

    def batch_delete_cases(self, case_ids):
        """批量删除测试用例"""
        cases = self._load_cases()
        cases = [case for case in cases if case.get('id') not in case_ids]
        self._save_cases(cases)
        return True
