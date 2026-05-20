import os
import json
from datetime import datetime
from util.file_util import FileUtil


class ApiTestResultManager:
    """接口测试结果管理器"""

    def __init__(self):
        self.results_dir = os.path.join(FileUtil.get_project_root(), 'reports', 'api_results')
        os.makedirs(self.results_dir, exist_ok=True)

    def save_result(self, task_id, results, test_names=None):
        """保存测试结果"""
        result_file = os.path.join(self.results_dir, f"{task_id}.json")

        summary = {
            'task_id': task_id,
            'total': len(results),
            'passed': sum(1 for r in results if r['passed']),
            'failed': sum(1 for r in results if not r['passed']),
            'executed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_names': test_names or [],
            'results': results
        }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary

    def get_result(self, task_id):
        """获取测试结果"""
        result_file = os.path.join(self.results_dir, f"{task_id}.json")

        if not os.path.exists(result_file):
            return None

        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_results(self, page=1, per_page=10):
        """列出所有测试结果（分页）"""
        results = []

        if not os.path.exists(self.results_dir):
            return results, 0

        for file in os.listdir(self.results_dir):
            if file.endswith('.json'):
                file_path = os.path.join(self.results_dir, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        results.append({
                            'task_id': data.get('task_id'),
                            'filename': file,
                            'total': data.get('total', 0),
                            'passed': data.get('passed', 0),
                            'failed': data.get('failed', 0),
                            'executed_at': data.get('executed_at'),
                            'test_names': data.get('test_names', [])
                        })
                except Exception:
                    continue

        results.sort(key=lambda x: x.get('executed_at', ''), reverse=True)

        total = len(results)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_results = results[start:end]

        return paginated_results, total

    def delete_result(self, task_id):
        """删除测试结果"""
        result_file = os.path.join(self.results_dir, f"{task_id}.json")
        if os.path.exists(result_file):
            os.remove(result_file)
            return True
        return False