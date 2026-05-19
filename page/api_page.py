import requests
import time
import json
from log.logger import LoggerUtil

logger = LoggerUtil.get_logger()


class ApiTester:
    """接口自动化测试核心类"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url
        self.session = requests.Session()
        self.variables = {}  # 存储变量，如token等
    
    def request(self, method, url, headers=None, data=None, params=None, json_data=None):
        """
        发送 HTTP 请求
        :param method: HTTP 方法 (GET, POST, PUT, DELETE 等)
        :param url: 请求 URL
        :param headers: 请求头
        :param data: 表单数据
        :param params: URL 参数
        :param json_data: JSON 数据
        :return: requests.Response 对象
        """
        full_url = f"{self.base_url}{url}" if self.base_url and not url.startswith('http')or url.startswith('https') else url
        
        logger.info(f"发送请求: {method} {full_url}")
        
        start_time = time.time()
        try:
            response = self.session.request(
                method=method,
                url=full_url,
                headers=headers or {},
                data=data,
                params=params,
                json=json_data,
                timeout=30
            )
            
            elapsed_time = (time.time() - start_time) * 1000  # 毫秒
            
            logger.info(f" 收到响应: {response.status_code} (耗时: {elapsed_time:.2f}ms)")
            logger.debug(f"响应内容: {response.text[:500]}")
            
            return response, elapsed_time
        except Exception as e:
            elapsed_time = (time.time() - start_time) * 1000
            logger.error(f"请求失败: {str(e)}")
            raise
    
    def extract_variables(self, response, extract_config):
        """
        从响应中提取变量
        :param response: requests.Response 对象
        :param extract_config: 提取配置
        """
        if not extract_config:
            return
            
        try:
            response_json = response.json()
            for var_name, json_path in extract_config.items():
                # 简单的JSON路径解析，支持如 "data.token" 这样的路径
                keys = json_path.split('.')
                value = response_json
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                
                if value is not None:
                    self.variables[var_name] = value
                    logger.info(f"提取变量: {var_name} = {value}")
                else:
                    logger.warning(f"无法提取变量: {var_name} (路径: {json_path})")
        except Exception as e:
            logger.warning(f"提取变量时出错: {str(e)}")
    
    def replace_variables(self, obj):
        """
        替换对象中的变量占位符
        :param obj: 要处理的对象（字符串、字典、列表等）
        :return: 处理后的对象
        """
        if isinstance(obj, str):
            # 替换 ${variable_name} 格式的变量
            for var_name, var_value in self.variables.items():
                placeholder = f"${{{var_name}}}"
                if placeholder in obj:
                    obj = obj.replace(placeholder, str(var_value))
            return obj
        elif isinstance(obj, dict):
            return {key: self.replace_variables(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.replace_variables(item) for item in obj]
        else:
            return obj
    
    def assert_response(self, response, elapsed_time, assertions):
        """
        断言验证
        :param response: requests.Response 对象
        :param elapsed_time: 响应时间 (毫秒)
        :param assertions: 断言规则
        :return: (passed, error_message)
        """
        errors = []
        
        # 1. 断言状态码
        if 'status_code' in assertions:
            expected_code = assertions['status_code']
            if response.status_code != expected_code:
                errors.append(f"状态码断言失败: 期望 {expected_code}, 实际 {response.status_code}")
        
        # 2. 断言响应时间
        if 'response_time' in assertions:
            time_assert = assertions['response_time']
            if 'less_than' in time_assert and elapsed_time > time_assert['less_than']:
                errors.append(f"响应时间断言失败: 期望 < {time_assert['less_than']}ms, 实际 {elapsed_time:.2f}ms")
        
        # 3. 断言响应体 JSON
        if 'json' in assertions and response.headers.get('Content-Type', '').startswith('application/json'):
            try:
                response_json = response.json()
                for key, expected_value in assertions['json'].items():
                    actual_value = response_json.get(key)
                    if actual_value != expected_value:
                        errors.append(f"JSON 断言失败 [{key}]: 期望 {expected_value}, 实际 {actual_value}")
            except Exception as e:
                errors.append(f"响应体 JSON 解析失败: {str(e)}")
        
        # 4. 断言响应体包含文本
        if 'contains' in assertions:
            for text in assertions['contains']:
                if text not in response.text:
                    errors.append(f"文本断言失败: 响应中未包含 '{text}'")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, None
    
    def run_api_test(self, test_case):
        """
        执行单个接口测试用例
        :param test_case: 测试用例配置
        :return: 测试结果字典
        """
        name = test_case.get('name', '未命名测试')
        description = test_case.get('description', '')
        request_config = test_case.get('request', {})
        assertions = test_case.get('assert', {})
        extract_config = test_case.get('extract', {})
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始执行接口测试: {name}")
        logger.info(f"描述: {description}")
        
        result = {
            'name': name,
            'description': description,
            'passed': False,
            'error': None,
            'status_code': None,
            'response_time': None,
            'response_body': None,
            'response_headers': None,
            'request_info': None
        }
        
        try:
            processed_request = self.replace_variables(request_config)
            
            response, elapsed_time = self.request(
                method=processed_request.get('method', 'GET').upper(),
                url=processed_request.get('url', ''),
                headers=processed_request.get('headers', {}),
                data=processed_request.get('data'),
                params=processed_request.get('params'),
                json_data=processed_request.get('data')
            )
            
            result['status_code'] = response.status_code
            result['response_time'] = f"{elapsed_time:.2f}ms"
            result['response_body'] = response.text
            
            try:
                result['response_json'] = response.json()
            except:
                result['response_json'] = None
            
            result['response_headers'] = dict(response.headers)
            result['request_info'] = {
                'method': processed_request.get('method', 'GET'),
                'url': processed_request.get('url', ''),
                'headers': processed_request.get('headers', {}),
                'data': processed_request.get('data')
            }
            
            if extract_config:
                self.extract_variables(response, extract_config)
            
            if assertions:
                passed, error_message = self.assert_response(response, elapsed_time, assertions)
                result['passed'] = passed
                result['error'] = error_message
            else:
                result['passed'] = response.status_code < 400
            
            if result['passed']:
                logger.info(f"测试通过: {name}")
            else:
                logger.error(f"测试失败: {name} - {result['error']}")
                
        except Exception as e:
            result['passed'] = False
            result['error'] = f"请求异常: {str(e)}"
            logger.error(f"测试异常: {name} - {str(e)}")
        
        return result
    
    def run_api_tests(self, test_cases):
        """
        批量执行接口测试
        :param test_cases: 测试用例列表
        :return: 测试结果列表
        """
        results = []
        for test_case in test_cases:
            result = self.run_api_test(test_case)
            results.append(result)
        
        return results
    
    def close(self):
        """关闭 session"""
        self.session.close()
