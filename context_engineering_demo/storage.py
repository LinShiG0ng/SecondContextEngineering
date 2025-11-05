"""
三层存储系统
实现短期、中期、长期三层记忆架构
"""

import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from collections import deque

from .utils import count_tokens
from . import config as default_config


class LayeredStorage:
    """三层记忆存储系统"""

    def __init__(self, workspace: str = None):
        """
        初始化三层存储

        Args:
            workspace: 工作空间目录
        """
        self.workspace = workspace or default_config.WORKSPACE_DIR

        # 创建工作空间目录
        Path(self.workspace).mkdir(parents=True, exist_ok=True)

        # 短期存储：最近N条消息（完整保留）
        self.short_term = deque(maxlen=default_config.SHORT_TERM_SIZE)

        # 中期存储：压缩后的历史消息
        self.mid_term = []

        # 长期存储：知识库文件路径
        self.long_term_path = Path(self.workspace) / "knowledge.json"

        # 原始消息备份（用于对比测试）
        self.original_messages = []

    def add_to_short_term(self, message: Dict):
        """
        添加消息到短期存储

        Args:
            message: 消息字典
        """
        # 添加时间戳
        if 'timestamp' not in message:
            message['timestamp'] = time.time()

        # 计算tokens
        if 'tokens' not in message:
            message['tokens'] = count_tokens(message.get('content', ''))

        # 添加到短期存储（自动处理容量限制）
        self.short_term.append(message)

        # 同时保存到原始消息备份
        self.original_messages.append(message)

    def promote_to_mid_term(self, compressed_summary: Dict):
        """
        将压缩后的摘要提升到中期存储

        Args:
            compressed_summary: 压缩摘要字典
        """
        # 添加时间戳
        if 'timestamp' not in compressed_summary:
            compressed_summary['timestamp'] = time.time()

        # 添加到中期存储
        self.mid_term.append(compressed_summary)

        # 限制中期存储大小
        if len(self.mid_term) > default_config.MID_TERM_SIZE:
            # 移除最旧的压缩摘要
            self.mid_term.pop(0)

    def save_to_long_term(self, key_info: Dict):
        """
        保存关键信息到长期知识库

        Args:
            key_info: 关键信息字典
        """
        # 加载现有知识库
        long_term_data = self.load_long_term()

        # 添加新信息
        timestamp = time.time()
        entry = {
            'timestamp': timestamp,
            'data': key_info
        }

        # 更新知识库
        if 'entries' not in long_term_data:
            long_term_data['entries'] = []

        long_term_data['entries'].append(entry)
        long_term_data['last_updated'] = timestamp

        # 保存到文件
        with open(self.long_term_path, 'w', encoding='utf-8') as f:
            json.dump(long_term_data, f, indent=2, ensure_ascii=False)

    def load_long_term(self) -> Dict:
        """
        加载长期知识库

        Returns:
            知识库字典
        """
        if not self.long_term_path.exists():
            return {
                'version': '1.0',
                'entries': [],
                'last_updated': None
            }

        try:
            with open(self.long_term_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载长期知识库失败: {e}")
            return {'version': '1.0', 'entries': []}

    def get_all_layers(self) -> Dict:
        """
        获取所有层的存储内容

        Returns:
            包含所有层的字典
        """
        return {
            'short_term': list(self.short_term),
            'mid_term': self.mid_term,
            'long_term': self.load_long_term()
        }

    def get_short_term_messages(self) -> List[Dict]:
        """
        获取短期存储的消息

        Returns:
            消息列表
        """
        return list(self.short_term)

    def get_mid_term_messages(self) -> List[Dict]:
        """
        获取中期存储的消息

        Returns:
            消息列表
        """
        return self.mid_term.copy()

    def get_original_messages(self) -> List[Dict]:
        """
        获取原始消息备份（用于对比测试）

        Returns:
            原始消息列表
        """
        return self.original_messages.copy()

    def clear_short_term(self):
        """清空短期存储"""
        self.short_term.clear()

    def clear_mid_term(self):
        """清空中期存储"""
        self.mid_term.clear()

    def clear_all(self):
        """清空所有存储（不包括长期知识库文件）"""
        self.short_term.clear()
        self.mid_term.clear()
        self.original_messages.clear()

    def calculate_tokens(self) -> Dict[str, int]:
        """
        计算各层的token数量

        Returns:
            各层token数量的字典
        """
        short_term_tokens = sum(
            msg.get('tokens', count_tokens(msg.get('content', '')))
            for msg in self.short_term
        )

        mid_term_tokens = sum(
            msg.get('tokens', count_tokens(msg.get('content', '')))
            for msg in self.mid_term
        )

        return {
            'short_term': short_term_tokens,
            'mid_term': mid_term_tokens,
            'total': short_term_tokens + mid_term_tokens
        }

    def get_statistics(self) -> Dict:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        tokens = self.calculate_tokens()

        return {
            'short_term_count': len(self.short_term),
            'short_term_tokens': tokens['short_term'],
            'mid_term_count': len(self.mid_term),
            'mid_term_tokens': tokens['mid_term'],
            'total_tokens': tokens['total'],
            'long_term_saved': self.long_term_path.exists(),
            'original_message_count': len(self.original_messages)
        }

    def export_to_json(self, filepath: Optional[str] = None) -> str:
        """
        导出所有存储到JSON文件

        Args:
            filepath: 导出文件路径（可选）

        Returns:
            导出的文件路径
        """
        if filepath is None:
            timestamp = int(time.time())
            filepath = Path(self.workspace) / f"storage_export_{timestamp}.json"
        else:
            filepath = Path(filepath)

        # 准备导出数据
        export_data = {
            'timestamp': time.time(),
            'storage': self.get_all_layers(),
            'statistics': self.get_statistics()
        }

        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def import_from_json(self, filepath: str):
        """
        从JSON文件导入存储

        Args:
            filepath: 导入文件路径
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # 恢复各层存储
            storage = import_data.get('storage', {})

            # 短期存储
            self.short_term.clear()
            for msg in storage.get('short_term', []):
                self.short_term.append(msg)

            # 中期存储
            self.mid_term = storage.get('mid_term', [])

            print(f"✅ 成功导入存储: {filepath}")

        except Exception as e:
            print(f"❌ 导入失败: {e}")


def create_storage(workspace: Optional[str] = None) -> LayeredStorage:
    """
    创建存储实例（便捷函数）

    Args:
        workspace: 工作空间目录

    Returns:
        LayeredStorage实例
    """
    return LayeredStorage(workspace)


if __name__ == "__main__":
    # 测试代码
    print("=== 三层存储系统测试 ===\n")

    storage = LayeredStorage()

    # 测试添加消息到短期存储
    print("1. 测试短期存储...")
    for i in range(10):
        message = {
            'role': 'user' if i % 2 == 0 else 'assistant',
            'content': f'这是第 {i+1} 条消息'
        }
        storage.add_to_short_term(message)

    print(f"   短期存储消息数: {len(storage.short_term)}")
    print(f"   （最多保留 {default_config.SHORT_TERM_SIZE} 条）\n")

    # 测试中期存储
    print("2. 测试中期存储...")
    summary = {
        'role': 'system',
        'content': '这是一个压缩摘要，包含了之前5条消息的要点',
        'type': 'compressed_summary',
        'original_count': 5
    }
    storage.promote_to_mid_term(summary)
    print(f"   中期存储消息数: {len(storage.mid_term)}\n")

    # 测试长期存储
    print("3. 测试长期存储...")
    key_info = {
        'type': 'project_metadata',
        'project_name': 'Context Engineering Demo',
        'key_decisions': [
            '使用三层存储架构',
            '支持多种LLM API'
        ]
    }
    storage.save_to_long_term(key_info)
    print(f"   长期知识库已保存\n")

    # 获取统计信息
    print("4. 存储统计:")
    stats = storage.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # 测试导出
    print("\n5. 测试导出...")
    export_path = storage.export_to_json()
    print(f"   已导出到: {export_path}")
