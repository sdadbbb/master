import os
import json
from datetime import datetime
from util.file_util import FileUtil


class ApiTestManager:
    """接口测试用例管理器"""

    def __init__(self):
        self.api_tests_dir = os.path.join(FileUtil.get_project_root(), 'config', 'api_tests')
        os.makedirs(self.api_tests_dir, exist_ok=True)
        self.api_tests_file = os.path.join(self.api_tests_dir, 'tests.json')
        self._ensure_tests_file()

    def _ensure_tests_file(self):
        """确保测试用例文件存在"""
        if not os.path.exists(self.api_tests_file):
            self._save_tests([])

    def _load_tests(self):
        """加载测试用例"""
        try:
            with open(self.api_tests_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_tests(self, tests):
        """保存测试用例"""
        with open(self.api_tests_file, 'w', encoding='utf-8') as f:
            json.dump(tests, f, ensure_ascii=False, indent=2)

    def get_all_tests(self):
        """获取所有测试用例"""
        return self._load_tests()

    def get_test_by_id(self, test_id):
        """根据ID获取测试用例"""
        tests = self._load_tests()
        for test in tests:
            if test.get('id') == test_id:
                return test
        return None

    def search_tests(self, keyword):
        """根据关键词模糊搜索测试用例
        
        Args:
            keyword (str): 搜索关键词，支持模糊匹配
            
        Returns:
            list: 匹配到的测试用例列表
        """
        if not keyword:
            return []
        
        tests = self._load_tests()
        keyword_lower = keyword.lower()
        
        # 支持按名称和描述进行模糊搜索
        matched_tests = [
            test for test in tests 
            if keyword_lower in test.get('name', '').lower() or 
               keyword_lower in test.get('description', '').lower()
        ]
        
        return matched_tests

    def add_test(self, test_data):
        """添加测试用例"""
        tests = self._load_tests()

        new_test = {
            'id': f"api_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            'name': test_data.get('name', ''),
            'description': test_data.get('description', ''),
            'request': test_data.get('request', {}),
            'extract': test_data.get('extract', {}),
            'assert': test_data.get('assert', {}),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        tests.append(new_test)
        self._save_tests(tests)
        return new_test

    def update_test(self, test_id, test_data):
        """更新测试用例"""
        tests = self._load_tests()

        for i, test in enumerate(tests):
            if test.get('id') == test_id:
                tests[i]['name'] = test_data.get('name', test['name'])
                tests[i]['description'] = test_data.get('description', test['description'])
                tests[i]['request'] = test_data.get('request', test['request'])
                tests[i]['extract'] = test_data.get('extract', test.get('extract', {}))
                tests[i]['assert'] = test_data.get('assert', test['assert'])
                tests[i]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_tests(tests)
                return tests[i]

        return None

    def delete_test(self, test_id):
        """删除测试用例"""
        tests = self._load_tests()
        tests = [test for test in tests if test.get('id') != test_id]
        self._save_tests(tests)
        return True

    def batch_delete_tests(self, test_ids):
        """批量删除测试用例"""
        tests = self._load_tests()
        tests = [test for test in tests if test.get('id') not in test_ids]
        self._save_tests(tests)
        return True