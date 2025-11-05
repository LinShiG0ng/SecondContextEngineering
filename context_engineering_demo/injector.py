"""
动态上下文注入器
实现智能上下文恢复和相关性检索
"""

import re
from typing import List, Dict, Optional
from .utils import calculate_similarity, count_tokens


class ContextInjector:
    """动态上下文注入器"""

    def __init__(self, relevance_threshold: float = 0.5):
        """
        初始化注入器

        Args:
            relevance_threshold: 相关性阈值
        """
        self.relevance_threshold = relevance_threshold

    def analyze_intent(self, query: str) -> Dict:
        """
        分析用户意图

        Args:
            query: 用户查询

        Returns:
            意图分析结果
        """
        intent = {
            'keywords': [],
            'entities': [],
            'intent_type': 'general',
            'requires_history': False
        }

        # 提取关键词（简单分词）
        words = re.findall(r'\w+', query.lower())
        intent['keywords'] = [w for w in words if len(w) > 2]

        # 检测意图类型
        if any(kw in query.lower() for kw in ['之前', '刚才', '前面', 'earlier', 'previous']):
            intent['intent_type'] = 'reference_history'
            intent['requires_history'] = True

        elif any(kw in query.lower() for kw in ['总结', '归纳', 'summarize', 'summary']):
            intent['intent_type'] = 'summarize'
            intent['requires_history'] = True

        elif any(kw in query.lower() for kw in ['错误', '问题', 'error', 'bug', 'issue']):
            intent['intent_type'] = 'debug'
            intent['requires_history'] = True

        elif '?' in query or '？' in query or any(kw in query.lower() for kw in ['what', 'how', 'why', '什么', '如何', '为什么']):
            intent['intent_type'] = 'question'

        return intent

    def find_relevant_segments(self, intent: Dict, history: List[Dict],
                               max_segments: int = 3) -> List[Dict]:
        """
        查找相关的历史片段

        Args:
            intent: 意图分析结果
            history: 历史消息列表
            max_segments: 最多返回的片段数

        Returns:
            相关片段列表
        """
        if not intent['requires_history']:
            return []

        scored_segments = []

        for msg in history:
            relevance = self.calculate_relevance(intent, msg)

            if relevance >= self.relevance_threshold:
                scored_segments.append({
                    'message': msg,
                    'relevance': relevance
                })

        # 按相关性排序
        scored_segments.sort(key=lambda x: x['relevance'], reverse=True)

        # 返回前N个最相关的片段
        return [s['message'] for s in scored_segments[:max_segments]]

    def calculate_relevance(self, intent: Dict, segment: Dict) -> float:
        """
        计算相关性分数

        Args:
            intent: 意图分析
            segment: 消息片段

        Returns:
            相关性分数（0-1）
        """
        content = segment.get('content', '').lower()
        score = 0.0

        # 1. 关键词匹配
        keyword_matches = sum(1 for kw in intent['keywords'] if kw in content)
        keyword_score = keyword_matches / max(len(intent['keywords']), 1)

        # 2. 意图类型匹配
        intent_score = 0.0
        if intent['intent_type'] == 'debug':
            if any(kw in content for kw in ['error', 'exception', 'bug', '错误', '异常']):
                intent_score = 0.5

        elif intent['intent_type'] == 'reference_history':
            # 更早的消息可能更相关
            intent_score = 0.3

        # 3. 角色权重（assistant的回答通常更有价值）
        role_weight = 0.3 if segment.get('role') == 'assistant' else 0.1

        # 综合评分
        score = keyword_score * 0.5 + intent_score * 0.3 + role_weight * 0.2

        return min(score, 1.0)

    async def inject_context(self, query: str, base_context: List[Dict],
                            full_history: Optional[List[Dict]] = None) -> List[Dict]:
        """
        智能注入上下文

        Args:
            query: 当前查询
            base_context: 基础上下文（已包含的消息）
            full_history: 完整历史（可选）

        Returns:
            注入后的上下文
        """
        if not full_history:
            return base_context

        # 分析意图
        intent = self.analyze_intent(query)

        # 如果不需要历史，直接返回
        if not intent['requires_history']:
            return base_context

        # 查找相关片段
        relevant_segments = self.find_relevant_segments(intent, full_history)

        if not relevant_segments:
            return base_context

        # 构建注入后的上下文
        # 策略：在base_context之前插入相关片段
        injected_context = []

        # 首先保留system prompts
        system_prompts = [m for m in base_context if m.get('role') == 'system']
        other_messages = [m for m in base_context if m.get('role') != 'system']

        # 组合：system + 相关片段 + 其他消息
        injected_context.extend(system_prompts)

        # 添加相关片段标记
        if relevant_segments:
            injected_context.append({
                'role': 'system',
                'content': f'📌 以下是 {len(relevant_segments)} 条相关历史记录（自动注入）',
                'type': 'injected_marker'
            })
            injected_context.extend(relevant_segments)

        injected_context.extend(other_messages)

        return injected_context


if __name__ == "__main__":
    # 测试代码
    print("=== 上下文注入器测试 ===\n")

    injector = ContextInjector()

    # 测试意图分析
    queries = [
        "之前讨论的Flask项目怎么样了？",
        "总结一下我们的对话",
        "main.py的错误解决了吗？",
        "创建一个新的Python项目"
    ]

    print("1. 意图分析测试:\n")
    for query in queries:
        intent = injector.analyze_intent(query)
        print(f"查询: {query}")
        print(f"  类型: {intent['intent_type']}")
        print(f"  需要历史: {intent['requires_history']}")
        print(f"  关键词: {intent['keywords'][:5]}")
        print()
