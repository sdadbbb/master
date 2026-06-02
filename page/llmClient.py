import json
import re
import requests
from util.file_util import FileUtil
from log.logger import LoggerUtil

logger = LoggerUtil.get_logger()


class LLMClient:
    """大模型客户端，兼容 OpenAI Chat Completions API"""

    def __init__(self):
        config = FileUtil.read_yaml(FileUtil.get_config_path())
        llm_config = config.get('llm', {})
        self.api_key = llm_config.get('api_key', '')
        self.base_url = llm_config.get('base_url', 'https://api.openai.com/v1').rstrip('/')
        self.model = llm_config.get('model', 'gpt-4o-mini')
        self.timeout = llm_config.get('timeout', 120)
        self.max_tokens = llm_config.get('max_tokens')
        self.temperature = llm_config.get('temperature', 0.3)

    def is_configured(self):
        """检查 API Key 是否已配置"""
        return bool(self.api_key and self.api_key != 'your-api-key-here')

    def chat(self, messages, temperature=None):
        """
        发送对话请求
        :param messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
        :return: 助手回复文本
        """
        if not self.is_configured():
            raise ValueError('请先在 config/config.yml 中配置 llm.api_key')

        url = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature if temperature is not None else self.temperature,
        }
        if self.max_tokens:
            payload['max_tokens'] = self.max_tokens

        token_info = self.max_tokens if self.max_tokens else '不限制'
        logger.info(f"调用大模型: {self.model}, 消息数: {len(messages)}, max_tokens: {token_info}")
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        choice = data['choices'][0]
        content = choice['message']['content']
        finish_reason = choice.get('finish_reason', '')

        logger.info(f"大模型回复长度: {len(content)} 字符, 结束原因: {finish_reason}")
        logger.info("=" * 80)
        logger.info("大模型完整回复内容:")
        logger.info(content)
        logger.info("=" * 80)
        return content

    def chat_with_tools(self, messages, tools=None, temperature=None):
        """
        发送支持工具调用的对话请求（Function Calling）
        :param messages: 消息列表
        :param tools: 工具规范列表，如果为 None 则不使用工具
        :param temperature: 温度参数
        :return: dict {
            'content': str,  # AI 的文本回复（如果有）
            'tool_calls': list,  # 工具调用列表（如果有）
            'raw_response': dict  # 原始响应
        }
        """
        if not self.is_configured():
            raise ValueError('请先在 config/config.yml 中配置 llm.api_key')

        url = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature if temperature is not None else self.temperature,
        }
        if self.max_tokens:
            payload['max_tokens'] = self.max_tokens
        
        # 添加工具规范
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'  # 让 AI 自动决定是否调用工具

        logger.info(f"调用大模型(带工具): {self.model}, 消息数: {len(messages)}, 工具数: {len(tools) if tools else 0}")
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        choice = data['choices'][0]
        message = choice['message']
        
        result = {
            'content': message.get('content'),
            'tool_calls': message.get('tool_calls', []),
            'raw_response': data
        }
        
        if result['tool_calls']:
            logger.info(f"AI 决定调用 {len(result['tool_calls'])} 个工具")
            for i, tool_call in enumerate(result['tool_calls'], 1):
                func_name = tool_call['function']['name']
                logger.info(f"  工具 {i}: {func_name}")
        elif result['content']:
            logger.info(f"AI 回复长度: {len(result['content'])} 字符")
        
        return result

    def chat_with_tools(self, messages, tools=None, temperature=None):
        """
        发送支持工具调用的对话请求（Function Calling）
        :param messages: 消息列表
        :param tools: 工具规范列表，如果为 None 则不使用工具
        :param temperature: 温度参数
        :return: dict {
            'content': str,  # AI 的文本回复（如果有）
            'tool_calls': list,  # 工具调用列表（如果有）
            'raw_response': dict  # 原始响应
        }
        """
        if not self.is_configured():
            raise ValueError('请先在 config/config.yml 中配置 llm.api_key')

        url = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature if temperature is not None else self.temperature,
        }
        if self.max_tokens:
            payload['max_tokens'] = self.max_tokens
        
        # 添加工具规范
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'  # 让 AI 自动决定是否调用工具

        logger.info(f"调用大模型(带工具): {self.model}, 消息数: {len(messages)}, 工具数: {len(tools) if tools else 0}")
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        choice = data['choices'][0]
        message = choice['message']
        
        result = {
            'content': message.get('content'),
            'tool_calls': message.get('tool_calls', []),
            'raw_response': data
        }
        
        if result['tool_calls']:
            logger.info(f"AI 决定调用 {len(result['tool_calls'])} 个工具")
            for i, tool_call in enumerate(result['tool_calls'], 1):
                func_name = tool_call['function']['name']
                logger.info(f"  工具 {i}: {func_name}")
        elif result['content']:
            logger.info(f"AI 回复长度: {len(result['content'])} 字符")
        
        return result

    def chat_with_tools(self, messages, tools=None, temperature=None):
        """
        发送支持工具调用的对话请求（Function Calling）
        :param messages: 消息列表
        :param tools: 工具规范列表，如果为 None 则不使用工具
        :param temperature: 温度参数
        :return: dict {
            'content': str,  # AI 的文本回复（如果有）
            'tool_calls': list,  # 工具调用列表（如果有）
            'raw_response': dict  # 原始响应
        }
        """
        if not self.is_configured():
            raise ValueError('请先在 config/config.yml 中配置 llm.api_key')

        url = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature if temperature is not None else self.temperature,
        }
        if self.max_tokens:
            payload['max_tokens'] = self.max_tokens
        
        # 添加工具规范
        if tools:
            payload['tools'] = tools
            payload['tool_choice'] = 'auto'  # 让 AI 自动决定是否调用工具

        logger.info(f"调用大模型(带工具): {self.model}, 消息数: {len(messages)}, 工具数: {len(tools) if tools else 0}")
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        choice = data['choices'][0]
        message = choice['message']
        
        result = {
            'content': message.get('content'),
            'tool_calls': message.get('tool_calls', []),
            'raw_response': data
        }
        
        if result['tool_calls']:
            logger.info(f"AI 决定调用 {len(result['tool_calls'])} 个工具")
            for i, tool_call in enumerate(result['tool_calls'], 1):
                func_name = tool_call['function']['name']
                logger.info(f"  工具 {i}: {func_name}")
        elif result['content']:
            logger.info(f"AI 回复长度: {len(result['content'])} 字符")
        
        return result

    @staticmethod
    def extract_json(text):
        """从模型回复中提取 JSON 对象"""
        text = text.strip()

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取第一个 { ... } 对象
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.error("=" * 80)
        logger.error("JSON 解析失败，大模型原始回复内容:")
        logger.error(text)
        logger.error("=" * 80)
        raise ValueError('无法从模型回复中解析 JSON 格式的测试用例')
