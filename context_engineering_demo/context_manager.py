"""
上下文管理器
负责整个上下文工程的协调和管理
"""

import time
from typing import List, Dict, Optional

from .storage import LayeredStorage
from .compressor import AU2Compressor
from .injector import ContextInjector
from .knowledge_base import KnowledgeBase
from .utils import count_tokens
from . import config as default_config


class ContextManager:
    """
    上下文管理器：负责整个上下文工程的协调

    核心功能：
    1. Token使用率监控
    2. 自动压缩触发
    3. 三层存储管理
    4. 上下文构建
    """

    def __init__(self, max_tokens: int = None, workspace: str = None):
        """
        初始化上下文管理器

        Args:
            max_tokens: 最大token限制（默认使用配置值）
            workspace: 工作空间目录
        """
        self.max_tokens = max_tokens or default_config.MAX_TOKENS

        # 初始化各个组件
        self.storage = LayeredStorage(workspace)
        self.compressor = AU2Compressor()
        self.injector = ContextInjector()
        self.knowledge_base = KnowledgeBase()

        # 统计信息
        self.stats = {
            'compressions': 0,
            'total_saved': 0,
            'avg_compression_ratio': 0.0,
            'compression_history': []
        }

    async def add_message(self, role: str, content: str,
                         metadata: Optional[Dict] = None) -> Dict:
        """
        添加新消息到上下文

        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
            metadata: 额外的元数据（可选）

        Returns:
            包含添加结果和当前状态的字典
        """
        # 构建消息
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            'tokens': count_tokens(content)
        }

        if metadata:
            message.update(metadata)

        # 添加到短期存储
        self.storage.add_to_short_term(message)

        # 检查是否需要压缩
        usage_rate = self.calculate_usage()
        should_compress = usage_rate >= default_config.AUTO_COMPACT_THRESHOLD

        result = {
            'success': True,
            'message': message,
            'usage_rate': usage_rate,
            'should_compress': should_compress,
            'current_tokens': self.storage.calculate_tokens()['total']
        }

        return result

    async def get_context(self, current_query: Optional[str] = None) -> List[Dict]:
        """
        获取完整的上下文（用于发送给LLM）

        Args:
            current_query: 当前查询（可选，用于智能注入）

        Returns:
            完整的上下文消息列表
        """
        context = []

        # 1. 加载长期知识库
        kb_message = self.knowledge_base.to_context_message()
        if kb_message['content']:  # 只有当知识库有内容时才添加
            context.append(kb_message)

        # 2. 加载中期存储（压缩摘要）
        mid_term_messages = self.storage.get_mid_term_messages()
        context.extend(mid_term_messages)

        # 3. 加载短期存储（最近消息）
        short_term_messages = self.storage.get_short_term_messages()
        context.extend(short_term_messages)

        # 4. 智能注入（如果有查询）
        if current_query:
            original_messages = self.storage.get_original_messages()
            context = await self.injector.inject_context(
                current_query,
                context,
                original_messages
            )

        return context

    def calculate_usage(self) -> float:
        """
        计算token使用率

        Returns:
            使用率（0-1之间）
        """
        tokens = self.storage.calculate_tokens()
        total_tokens = tokens['total']

        return total_tokens / self.max_tokens if self.max_tokens > 0 else 0.0

    async def compress_if_needed(self, force: bool = False) -> Optional[Dict]:
        """
        检查并在需要时执行压缩

        Args:
            force: 是否强制压缩

        Returns:
            压缩结果（如果执行了压缩），否则返回None
        """
        usage_rate = self.calculate_usage()

        # 检查是否需要压缩
        if not force and usage_rate < default_config.AUTO_COMPACT_THRESHOLD:
            return None

        # 执行压缩
        return await self.compress()

    async def compress(self) -> Dict:
        """
        执行压缩

        Returns:
            压缩结果字典
        """
        # 获取当前所有消息
        all_messages = self.storage.get_short_term_messages()

        if len(all_messages) < 2:
            return {
                'success': False,
                'message': '消息数量不足，无需压缩'
            }

        # 执行AU2压缩
        compression_result = await self.compressor.compress(all_messages)

        # 提取压缩摘要和系统提示词
        compressed_messages = compression_result['compressed_messages']
        statistics = compression_result['statistics']

        # ⭐ 将压缩摘要提升到中期存储
        # 注意：system prompts已经包含在compressed_messages中
        summary_message = None
        for msg in compressed_messages:
            if msg.get('type') == 'compressed_summary':
                summary_message = msg
                break

        if summary_message:
            self.storage.promote_to_mid_term(summary_message)

        # 清空短期存储，准备接收新消息
        self.storage.clear_short_term()

        # 将最近的几条重要消息重新加入短期存储
        for msg in compressed_messages:
            if msg.get('type') != 'compressed_summary' and msg.get('role') != 'system':
                self.storage.add_to_short_term(msg)

        # 更新统计信息
        self.stats['compressions'] += 1
        self.stats['total_saved'] += statistics['tokens_saved']

        # 计算平均压缩率
        self.stats['compression_history'].append(statistics['compression_ratio'])
        self.stats['avg_compression_ratio'] = sum(self.stats['compression_history']) / len(self.stats['compression_history'])

        # 更新知识库
        if compression_result.get('entities'):
            self.knowledge_base.update({
                'entities': compression_result['entities']
            })

        return {
            'success': True,
            'statistics': statistics,
            'compressed_messages': compressed_messages
        }

    def get_statistics(self) -> Dict:
        """
        获取完整的统计信息

        Returns:
            统计信息字典
        """
        tokens = self.storage.calculate_tokens()
        usage_rate = self.calculate_usage()

        return {
            'conversation': {
                'total_messages': len(self.storage.get_original_messages()),
                'user_messages': len([m for m in self.storage.get_original_messages() if m.get('role') == 'user']),
                'assistant_messages': len([m for m in self.storage.get_original_messages() if m.get('role') == 'assistant']),
                'current_tokens': tokens['total'],
                'max_tokens': self.max_tokens,
                'usage_percentage': usage_rate
            },
            'compression': {
                'count': self.stats['compressions'],
                'total_saved': self.stats['total_saved'],
                'avg_ratio': self.stats['avg_compression_ratio'],
                'retention_rate': 0.95  # 简化：假设95%
            },
            'storage': self.storage.get_statistics()
        }

    def reset(self):
        """重置上下文管理器"""
        self.storage.clear_all()
        self.stats = {
            'compressions': 0,
            'total_saved': 0,
            'avg_compression_ratio': 0.0,
            'compression_history': []
        }

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        导出上下文到JSON

        Args:
            filepath: 导出文件路径（可选）

        Returns:
            导出文件路径
        """
        return self.storage.export_to_json(filepath)

    def import_json(self, filepath: str):
        """
        从JSON导入上下文

        Args:
            filepath: 导入文件路径
        """
        self.storage.import_from_json(filepath)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test_context_manager():
        print("=== 上下文管理器测试 ===\n")

        manager = ContextManager(max_tokens=2000)  # 使用较小的限制方便测试

        # 添加一系列消息
        print("1. 添加消息测试...\n")

        # System prompt
        await manager.add_message(
            "system",
            "你是一个Python编程助手"
        )

        # 用户对话
        conversations = [
            ("user", "创建一个Flask项目"),
            ("assistant", "好的，我来帮你创建Flask项目。首先需要安装Flask库..." * 20),
            ("user", "添加用户认证功能"),
            ("assistant", "我们可以使用Flask-Login来实现用户认证功能..." * 20),
            ("user", "main.py第42行出现TypeError"),
            ("assistant", "这个TypeError是因为类型不匹配。我们需要检查..." * 20),
            ("user", "如何优化数据库查询？"),
            ("assistant", "优化数据库查询可以从以下几个方面入手..." * 20),
        ]

        for role, content in conversations:
            result = await manager.add_message(role, content)
            usage = result['usage_rate']
            print(f"[{role}] Token使用率: {usage*100:.1f}% ", end='')

            if result['should_compress']:
                print("🔄 触发压缩！")
                compression_result = await manager.compress_if_needed()
                if compression_result and compression_result['success']:
                    stats = compression_result['statistics']
                    print(f"   压缩完成: {stats['tokens_saved']:,} tokens saved")
            else:
                print()

        # 显示最终统计
        print("\n2. 最终统计信息:")
        from .utils import print_statistics
        print_statistics(manager.get_statistics())

        # 测试获取上下文
        print("\n3. 获取上下文测试...")
        context = await manager.get_context("总结一下我们的对话")
        print(f"   上下文消息数: {len(context)}")
        print(f"   包含类型: {set(m.get('type', 'normal') for m in context)}")

    asyncio.run(test_context_manager())
