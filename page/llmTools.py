"""
LLM 工具定义模块
定义 AI 可以调用的本地方法（Function Calling）
"""
import json
import os
from page.apiTestManager import ApiTestManager
from page.uiTestCaseManager import UITestCaseManager
from page.apiTestReusltManager import ApiTestResultManager
from page.uiTestResultManager import UITestResultManager
from log.logger import LoggerUtil

logger = LoggerUtil.get_logger()

# 初始化管理器实例
api_manager = ApiTestManager()
ui_manager = UITestCaseManager()
api_result_manager = ApiTestResultManager()
ui_result_manager = UITestResultManager()


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


# ==================== 分析类工具规范定义 ====================

ANALYSIS_TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_api_test_cases",
            "description": "获取系统中所有API接口测试用例的完整列表",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ui_test_cases",
            "description": "获取系统中所有UI自动化测试用例的完整列表",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_api_test_results",
            "description": "获取最近的API测试执行结果汇总列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "获取最近几条执行记录，默认10条"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ui_test_results",
            "description": "获取最近的UI测试执行结果汇总列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "获取最近几条执行记录，默认10条"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_test_result_detail",
            "description": "获取指定测试任务的详细执行结果，包含每条用例的通过/失败详情、错误信息、响应数据等",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务ID，例如 llm_20260602093500"
                    }
                },
                "required": ["task_id"]
            }
        }
    }
]


# ==================== 分析类工具执行函数 ====================

def execute_get_api_test_cases(args):
    """获取系统中所有API接口测试用例"""
    try:
        tests = api_manager.get_all_tests()
        simplified = []
        for t in tests:
            simplified.append({
                'id': t.get('id', ''),
                'name': t.get('name', ''),
                'description': t.get('description', ''),
                'method': t.get('request', {}).get('method', 'GET'),
                'url': t.get('request', {}).get('url', ''),
                'headers': t.get('request', {}).get('headers', {}),
                'data': t.get('request', {}).get('data', {}),
                'assert_rules': t.get('assert', {}),
                'extract': t.get('extract', {}),
                'created_at': t.get('created_at', ''),
                'updated_at': t.get('updated_at', '')
            })
        logger.info(f"获取到 {len(simplified)} 个API测试用例")
        return {'success': True, 'total': len(simplified), 'test_cases': simplified}
    except Exception as e:
        logger.error(f"获取API测试用例失败: {str(e)}")
        return {'success': False, 'error': str(e)}


def execute_get_ui_test_cases(args):
    """获取系统中所有UI测试用例"""
    try:
        cases = ui_manager.get_all_cases()
        simplified = []
        for c in cases:
            simplified.append({
                'id': c.get('id', ''),
                'name': c.get('name', ''),
                'description': c.get('description', ''),
                'url': c.get('url', ''),
                'steps_count': len(c.get('steps', [])),
                'steps': c.get('steps', []),
                'created_at': c.get('created_at', ''),
                'updated_at': c.get('updated_at', '')
            })
        logger.info(f"获取到 {len(simplified)} 个UI测试用例")
        return {'success': True, 'total': len(simplified), 'test_cases': simplified}
    except Exception as e:
        logger.error(f"获取UI测试用例失败: {str(e)}")
        return {'success': False, 'error': str(e)}


def execute_get_api_test_results(args):
    """获取最近的API测试执行结果"""
    try:
        limit = args.get('limit', 10)
        results, total = api_result_manager.list_results(page=1, per_page=limit)
        logger.info(f"获取到 {total} 条API测试结果")
        return {'success': True, 'total': total, 'results': results}
    except Exception as e:
        logger.error(f"获取API测试结果失败: {str(e)}")
        return {'success': False, 'error': str(e)}


def execute_get_ui_test_results(args):
    """获取最近的UI测试执行结果"""
    try:
        limit = args.get('limit', 10)
        results, total = ui_result_manager.list_results(page=1, per_page=limit)
        logger.info(f"获取到 {total} 条UI测试结果")
        return {'success': True, 'total': total, 'results': results}
    except Exception as e:
        logger.error(f"获取UI测试结果失败: {str(e)}")
        return {'success': False, 'error': str(e)}


def execute_get_test_result_detail(args):
    """获取指定测试任务的详细执行结果"""
    try:
        task_id = args.get('task_id', '')
        # 先在API结果中查找
        result = api_result_manager.get_result(task_id)
        if result:
            logger.info(f"找到API测试结果: {task_id}")
            return {'success': True, 'type': 'api', 'result': result}
        # 再在UI结果中查找
        result = ui_result_manager.get_result(task_id)
        if result:
            logger.info(f"找到UI测试结果: {task_id}")
            return {'success': True, 'type': 'ui', 'result': result}
        return {'success': False, 'error': f'未找到任务 {task_id} 的执行结果'}
    except Exception as e:
        logger.error(f"获取测试结果详情失败: {str(e)}")
        return {'success': False, 'error': str(e)}


# 工具名称到执行函数的映射
TOOL_EXECUTORS = {
    'generate_api_test_case': execute_generate_api_test_case,
    'generate_ui_test_case': execute_generate_ui_test_case,
    'batch_generate_api_cases': execute_batch_generate_api_cases,
    'batch_generate_ui_cases': execute_batch_generate_ui_cases,
    'get_api_test_cases': execute_get_api_test_cases,
    'get_ui_test_cases': execute_get_ui_test_cases,
    'get_api_test_results': execute_get_api_test_results,
    'get_ui_test_results': execute_get_ui_test_results,
    'get_test_result_detail': execute_get_test_result_detail
}


def get_tool_executor(tool_name):
    """获取工具执行函数"""
    return TOOL_EXECUTORS.get(tool_name)
