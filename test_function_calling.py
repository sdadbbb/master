"""
AI Function Calling 功能测试脚本
用于验证智能生成功能是否正常工作
"""
import requests
import json

# Flask 服务器地址
BASE_URL = "http://localhost:5000"

def test_smart_generate():
    """测试 AI 智能生成功能"""
    
    # 测试用例 1: 简单的登录功能
    print("=" * 80)
    print("测试 1: 用户登录功能")
    print("=" * 80)
    
    payload = {
        "requirement": "实现一个用户登录功能，支持用户名密码登录，登录成功后跳转到首页，失败时显示错误提示",
        "extra_prompt": "请生成接口和UI测试用例"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/llm/smart_generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"AI 回复: {result['data'].get('ai_content', 'N/A')[:200]}...")
            print(f"工具调用次数: {result['data']['tool_calls_count']}")
            print(f"成功: {result['data']['success_count']}, 失败: {result['data']['failed_count']}")
            
            if result['data']['tool_results']:
                print("\n工具执行结果:")
                for i, tool_result in enumerate(result['data']['tool_results'], 1):
                    print(f"  {i}. {tool_result['tool']}: {'✅' if tool_result['success'] else '❌'}")
                    if tool_result['success']:
                        print(f"     - {tool_result['result'].get('message', 'N/A')}")
                    else:
                        print(f"     - 错误: {tool_result['result'].get('error', 'N/A')}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应: {response.text}")
    
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
    
    print("\n")
    
    # 测试用例 2: 批量生成
    print("=" * 80)
    print("测试 2: 用户管理功能（批量）")
    print("=" * 80)
    
    payload2 = {
        "requirement": "实现用户管理功能，包括：创建用户、删除用户、修改用户信息、查询用户列表",
        "extra_prompt": "请批量生成多个接口测试用例"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/llm/smart_generate",
            json=payload2,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 请求成功!")
            print(f"工具调用次数: {result['data']['tool_calls_count']}")
            print(f"成功: {result['data']['success_count']}, 失败: {result['data']['failed_count']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    
    except Exception as e:
        print(f"❌ 异常: {str(e)}")


def check_server_status():
    """检查服务器状态"""
    try:
        response = requests.get(f"{BASE_URL}/api/llm/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"✅ 服务器运行正常")
            print(f"   LLM 配置: {'已配置' if config['data']['configured'] else '未配置'}")
            print(f"   模型: {config['data']['model']}")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器: {BASE_URL}")
        print(f"   请先启动 Flask 应用: python web_ui/app.py")
        return False
    except Exception as e:
        print(f"❌ 检查服务器状态失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("AI Function Calling 功能测试")
    print("=" * 80 + "\n")
    
    # 检查服务器状态
    if not check_server_status():
        exit(1)
    
    print("\n开始测试...\n")
    
    # 运行测试
    test_smart_generate()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80 + "\n")
