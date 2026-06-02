"""
LLM 工具定义模块
定义 AI 可以调用的本地方法（Function Calling）
"""
import json
from page.apiTestManager import ApiTestManager
from page.uiTestCaseManager import UITestCaseManager
from log.logger import LoggerUtil

logger = LoggerUtil.get_logger()

# 初始化管理器实例
api_manager = ApiTestManager()
ui_manager = UITestCaseManager()


# ==================== 工具规范定义 ====================

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "generate_api_test_case",
            "description": "根据需求描述生成接口测试用例并保存到平台",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "测试用例名称，例如：用户登录接口测试"
                    },
                    "description": {
                        "type": "string",
                        "description": "测试用例描述"
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                        "description": "HTTP 请求方法"
                    },
                    "url": {
                        "type": "string",
                        "description": "API URL，可以是完整URL或相对路径"
                    },
                    "headers": {
                        "type": "object",
                        "description": "请求头，例如：{\"Content-Type\": \"application/json\"}"
                    },
                    "data": {
                        "type": "object",
                        "description": "请求数据/参数"
                    },
                    "assert_status_code": {
                        "type": "integer",
                        "description": "期望的响应状态码，默认 200"
                    },
                    "assert_response_time": {
                        "type": "integer",
                        "description": "期望的最大响应时间（毫秒），默认 3000"
                    }
                },
                "required": ["name", "method", "url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_ui_test_case",
            "description": "根据需求描述生成UI自动化测试用例并保存到平台",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "测试用例名称，例如：用户登录功能测试"
                    },
                    "description": {
                        "type": "string",
                        "description": "测试用例描述"
                    },
                    "url": {
                        "type": "string",
                        "description": "起始URL，测试开始的页面地址"
                    },
                    "steps": {
                        "type": "array",
                        "description": "测试步骤列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "action": {
                                    "type": "string",
                                    "description": "操作类型，例如：go_url, click_element, input_element, wait, assert_text_exists"
                                },
                                "params": {
                                    "type": "object",
                                    "description": "操作参数，根据 action 不同而不同"
                                }
                            },
                            "required": ["action", "params"]
                        }
                    }
                },
                "required": ["name", "url", "steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "batch_generate_api_cases",
            "description": "批量生成多个接口测试用例",
            "parameters": {
                "type": "object",
                "properties": {
                    "cases": {
                        "type": "array",
                        "description": "测试用例列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "method": {"type": "string"},
                                "url": {"type": "string"},
                                "headers": {"type": "object"},
                                "data": {"type": "object"}
                            },
                            "required": ["name", "method", "url"]
                        }
                    }
                },
                "required": ["cases"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "batch_generate_ui_cases",
            "description": "批量生成多个UI测试用例",
            "parameters": {
                "type": "object",
                "properties": {
                    "cases": {
                        "type": "array",
                        "description": "UI测试用例列表",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "url": {"type": "string"},
                                "steps": {"type": "array"}
                            },
                            "required": ["name", "url", "steps"]
                        }
                    }
                },
                "required": ["cases"]
            }
        }
    }
]


# ==================== 工具执行函数 ====================

def execute_generate_api_test_case(args):
    """执行生成单个接口测试用例"""
    try:
        test_data = {
            'name': args.get('name', '未命名接口用例'),
            'description': args.get('description', ''),
            'request': {
                'method': args.get('method', 'GET'),
                'url': args.get('url', ''),
                'headers': args.get('headers', {}),
                'data': args.get('data', {})
            },
            'extract': {},
            'assert': {
                'status_code': args.get('assert_status_code', 200),
                'response_time': {'less_than': args.get('assert_response_time', 3000)}
            }
        }
        
        saved_case = api_manager.add_test(test_data)
        logger.info(f"✅ 已生成接口用例: {saved_case['name']} (ID: {saved_case['id']})")
        
        return {
            'success': True,
            'case_id': saved_case['id'],
            'case_name': saved_case['name'],
            'message': f'接口用例已保存: {saved_case["name"]}'
        }
    except Exception as e:
        logger.error(f"❌ 生成接口用例失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def execute_generate_ui_test_case(args):
    """执行生成单个UI测试用例"""
    try:
        case_data = {
            'name': args.get('name', '未命名UI用例'),
            'description': args.get('description', ''),
            'url': args.get('url', ''),
            'steps': args.get('steps', [])
        }
        
        saved_case = ui_manager.add_case(case_data)
        logger.info(f"✅ 已生成UI用例: {saved_case['name']} (ID: {saved_case['id']})")
        
        return {
            'success': True,
            'case_id': saved_case['id'],
            'case_name': saved_case['name'],
            'message': f'UI用例已保存: {saved_case["name"]}'
        }
    except Exception as e:
        logger.error(f"❌ 生成UI用例失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def execute_batch_generate_api_cases(args):
    """执行批量生成接口测试用例"""
    cases = args.get('cases', [])
    results = []
    
    for i, case_args in enumerate(cases, 1):
        logger.info(f"正在生成第 {i}/{len(cases)} 个接口用例...")
        result = execute_generate_api_test_case(case_args)
        results.append(result)
    
    success_count = sum(1 for r in results if r.get('success'))
    logger.info(f"✅ 批量生成完成: {success_count}/{len(cases)} 个接口用例成功")
    
    return {
        'success': True,
        'total': len(cases),
        'success_count': success_count,
        'failed_count': len(cases) - success_count,
        'results': results
    }


def execute_batch_generate_ui_cases(args):
    """执行批量生成UI测试用例"""
    cases = args.get('cases', [])
    results = []
    
    for i, case_args in enumerate(cases, 1):
        logger.info(f"正在生成第 {i}/{len(cases)} 个UI用例...")
        result = execute_generate_ui_test_case(case_args)
        results.append(result)
    
    success_count = sum(1 for r in results if r.get('success'))
    logger.info(f"✅ 批量生成完成: {success_count}/{len(cases)} 个UI用例成功")
    
    return {
        'success': True,
        'total': len(cases),
        'success_count': success_count,
        'failed_count': len(cases) - success_count,
        'results': results
    }


# 工具名称到执行函数的映射
TOOL_EXECUTORS = {
    'generate_api_test_case': execute_generate_api_test_case,
    'generate_ui_test_case': execute_generate_ui_test_case,
    'batch_generate_api_cases': execute_batch_generate_api_cases,
    'batch_generate_ui_cases': execute_batch_generate_ui_cases
}


def get_tool_executor(tool_name):
    """获取工具执行函数"""
    return TOOL_EXECUTORS.get(tool_name)
