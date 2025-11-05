"""
LLM API统一客户端
支持OpenAI、Anthropic、Ollama等多种API提供商
"""

import asyncio
import httpx
from typing import List, Dict, Optional, AsyncIterator
import time

from .utils import count_tokens, count_tokens_tiktoken


class LLMClient:
    """统一的LLM客户端接口"""

    def __init__(self, config: Dict):
        """
        初始化LLM客户端

        Args:
            config: 配置字典，包含provider、model、api_key等
        """
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        self.temperature = config.get('temperature', 0.7)
        self.timeout = config.get('timeout', 60)
        self.max_retries = config.get('max_retries', 3)

        # 根据provider设置默认base_url
        if not self.base_url:
            if self.provider == 'openai':
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == 'anthropic':
                self.base_url = "https://api.anthropic.com/v1"
            elif self.provider == 'ollama':
                self.base_url = "http://localhost:11434"

        # 统计信息
        self.stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'response_times': []
        }

    async def chat(self, messages: List[Dict], stream: bool = False) -> str:
        """
        发送聊天请求（统一接口）

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            stream: 是否使用流式输出

        Returns:
            模型的响应内容
        """
        start_time = time.time()

        try:
            if self.provider == 'openai':
                response = await self._chat_openai(messages, stream)
            elif self.provider == 'anthropic':
                response = await self._chat_anthropic(messages, stream)
            elif self.provider == 'ollama':
                response = await self._chat_ollama(messages, stream)
            else:
                response = await self._chat_custom(messages, stream)

            # 更新统计信息
            response_time = time.time() - start_time
            self.stats['total_requests'] += 1
            self.stats['response_times'].append(response_time)

            return response

        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    async def _chat_openai(self, messages: List[Dict], stream: bool) -> str:
        """
        OpenAI API调用

        Args:
            messages: 消息列表
            stream: 是否流式输出

        Returns:
            响应内容
        """
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": stream
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if stream:
                # 流式输出
                response_text = ""
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                import json
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        response_text += content
                                        # 实时打印（可选）
                                        print(content, end='', flush=True)
                            except:
                                continue
                return response_text
            else:
                # 非流式输出
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content']

    async def _chat_anthropic(self, messages: List[Dict], stream: bool) -> str:
        """
        Anthropic API调用（Claude）

        Args:
            messages: 消息列表
            stream: 是否流式输出

        Returns:
            响应内容
        """
        url = f"{self.base_url}/messages"

        # Anthropic API需要分离system消息
        system_messages = [m['content'] for m in messages if m['role'] == 'system']
        other_messages = [m for m in messages if m['role'] != 'system']

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": other_messages,
            "max_tokens": 4096,
            "temperature": self.temperature,
            "stream": stream
        }

        # 添加system消息（如果有）
        if system_messages:
            payload['system'] = '\n\n'.join(system_messages)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if stream:
                # 流式输出
                response_text = ""
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            try:
                                import json
                                chunk = json.loads(data)
                                if chunk.get('type') == 'content_block_delta':
                                    delta = chunk.get('delta', {})
                                    content = delta.get('text', '')
                                    if content:
                                        response_text += content
                                        print(content, end='', flush=True)
                            except:
                                continue
                return response_text
            else:
                # 非流式输出
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                return result['content'][0]['text']

    async def _chat_ollama(self, messages: List[Dict], stream: bool) -> str:
        """
        Ollama API调用（本地模型）

        Args:
            messages: 消息列表
            stream: 是否流式输出

        Returns:
            响应内容
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if stream:
                # 流式输出
                response_text = ""
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                import json
                                chunk = json.loads(line)
                                content = chunk.get('message', {}).get('content', '')
                                if content:
                                    response_text += content
                                    print(content, end='', flush=True)
                                if chunk.get('done', False):
                                    break
                            except:
                                continue
                return response_text
            else:
                # 非流式输出
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result['message']['content']

    async def _chat_custom(self, messages: List[Dict], stream: bool) -> str:
        """
        自定义API调用（兼容OpenAI格式）

        Args:
            messages: 消息列表
            stream: 是否流式输出

        Returns:
            响应内容
        """
        # 默认使用OpenAI格式
        return await self._chat_openai(messages, stream)

    async def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否成功
        """
        try:
            test_messages = [
                {"role": "user", "content": "Hi"}
            ]

            response = await self.chat(test_messages, stream=False)

            if response:
                print(f"✅ 连接成功！模型响应正常。")
                print(f"   响应示例: {response[:50]}...")
                return True
            else:
                print(f"❌ 连接失败：模型无响应")
                return False

        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            return False

    def count_tokens(self, text: str) -> int:
        """
        计算token数量

        Args:
            text: 文本内容

        Returns:
            token数量
        """
        # 根据provider使用不同的计数方法
        if self.provider == 'openai':
            return count_tokens_tiktoken(text, self.model)
        else:
            return count_tokens(text)

    def estimate_cost(self, input_tokens: int, output_tokens: int = 0) -> float:
        """
        估算API调用成本

        Args:
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            预估成本（美元）
        """
        from .config import MODEL_PRICING

        pricing = MODEL_PRICING.get(self.model, {'input': 0.001, 'output': 0.002})

        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']

        return input_cost + output_cost

    def get_model_info(self) -> Dict:
        """
        获取模型信息

        Returns:
            模型信息字典
        """
        from .config import MODEL_MAX_TOKENS, MODEL_PRICING

        return {
            'provider': self.provider,
            'model': self.model,
            'max_tokens': MODEL_MAX_TOKENS.get(self.model, 8000),
            'pricing': MODEL_PRICING.get(self.model, {'input': 0.001, 'output': 0.002}),
            'base_url': self.base_url
        }

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        avg_response_time = (
            sum(self.stats['response_times']) / len(self.stats['response_times'])
            if self.stats['response_times'] else 0
        )

        return {
            'total_requests': self.stats['total_requests'],
            'total_tokens': self.stats['total_tokens'],
            'estimated_cost': self.stats['total_cost'],
            'avg_response_time': avg_response_time
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_cost': 0.0,
            'response_times': []
        }


async def create_client_from_config(config: Dict) -> LLMClient:
    """
    从配置创建LLM客户端（便捷函数）

    Args:
        config: 配置字典

    Returns:
        LLM客户端实例
    """
    llm_config = config.get('llm', {})
    return LLMClient(llm_config)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test_client():
        print("=== LLM客户端测试 ===\n")

        # 测试OpenAI（需要API key）
        config = {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'api_key': 'your-api-key-here',  # 替换为实际的API key
            'temperature': 0.7
        }

        client = LLMClient(config)

        # 测试连接
        print("测试连接...")
        success = await client.test_connection()

        if success:
            # 测试对话
            print("\n测试对话...")
            messages = [
                {"role": "user", "content": "用一句话介绍Python"}
            ]

            response = await client.chat(messages, stream=False)
            print(f"响应: {response}")

            # 显示统计信息
            print(f"\n统计信息: {client.get_stats()}")

    # 运行测试
    # asyncio.run(test_client())
    print("提示：请在实际使用时配置API key并取消注释上面的测试代码")
