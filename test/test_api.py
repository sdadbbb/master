import pytest
import yaml
from util.file_util import FileUtil
from page.api_page import ApiTester
from log.logger import LoggerUtil

logger = LoggerUtil.get_logger()


@pytest.fixture(scope="function")
def api_tester():
    """创建 API 测试器"""
    tester = ApiTester()
    yield tester
    tester.close()


def load_api_test_cases():
    """加载接口测试用例"""
    config = FileUtil.read_yaml(FileUtil.get_config_path())
    base_url = config.get('api', {}).get('base_url', '')

    # 从配置文件加载接口测试用例
    api_config_path = FileUtil.get_config_path().replace('config.yml', 'api_tests.yml')
    try:
        with open(api_config_path, 'r', encoding='utf-8') as f:
            api_config = yaml.safe_load(f)

        test_cases = api_config.get('api_tests', [])
        logger.info(f"加载了 {len(test_cases)} 个接口测试用例")
        return test_cases
    except Exception as e:
        logger.warning(f"加载接口测试用例失败: {str(e)}")
        return []


class TestAPI:
    """接口自动化测试类"""

    def test_api_login(self, api_tester):
        """测试登录接口"""
        test_case = {
            'name': '用户登录',
            'description': '验证用户登录功能',
            'request': {
                'method': 'POST',
                'url': 'http://192.168.2.114:94/api/login',
                'headers': {
                    'Content-Type': 'application/json'
                },
                'data': {
                    'username': 'superadmin',
                    'password': 'admin123'
                }
            },
            'assert': {
                'status_code': 200,
                'response_time': {
                    'less_than': 1000
                },
                'json': {
                    'success': True
                }
            }
        }

        result = api_tester.run_api_test(test_case)
        assert result['passed'], f"测试失败: {result['error']}"

    def test_api_batch(self, api_tester):
        """批量测试接口"""
        test_cases = load_api_test_cases()

        if not test_cases:
            pytest.skip("没有配置接口测试用例")

        results = api_tester.run_api_tests(test_cases)

        # 统计结果
        passed_count = sum(1 for r in results if r['passed'])
        failed_count = len(results) - passed_count

        logger.info(f"\n{'='*60}")
        logger.info(f" 接口测试汇总:")
        logger.info(f"   总计: {len(results)} 个")
        logger.info(f"   通过: {passed_count} 个")
        logger.info(f"   失败: {failed_count} 个")

        # 输出失败用例详情
        if failed_count > 0:
            logger.error(" 失败的测试用例:")
            for result in results:
                if not result['passed']:
                    logger.error(f"   - {result['name']}: {result['error']}")

        assert failed_count == 0, f"有 {failed_count} 个接口测试失败"
