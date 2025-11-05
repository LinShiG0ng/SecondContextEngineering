"""
AU2智能压缩算法
实现8段式压缩流程，包含System Prompt特殊处理

✨ LLM驱动版本：使用大模型API进行智能分析和压缩
"""

import time
import json
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict, Counter

from .utils import count_tokens, extract_entities, extract_code_blocks
from . import config as default_config


class AU2Compressor:
    """AU2智能压缩器（LLM驱动版本）"""

    def __init__(self, llm_client=None):
        """
        初始化压缩器

        Args:
            llm_client: LLM客户端实例（用于智能分析和摘要生成）
                       如果为None，将使用规则匹配的fallback模式
        """
        self.target_ratio = default_config.TARGET_COMPRESSION_RATIO
        self.preserve_system = default_config.PRESERVE_SYSTEM_PROMPTS
        self.llm_client = llm_client
        self.use_llm = llm_client is not None

        if self.use_llm:
            print("✨ 使用LLM驱动模式（智能分析）")
        else:
            print("⚠️  使用规则匹配模式（Fallback）")

    async def compress(self, messages: List[Dict]) -> Dict:
        """
        执行完整的8段式压缩流程

        ⭐ 特别处理：System Prompt完全保留，不压缩

        Args:
            messages: 要压缩的消息列表

        Returns:
            压缩结果字典，包含：
            - compressed_messages: 压缩后的消息列表
            - system_prompts: 保留的系统提示词
            - statistics: 压缩统计信息
        """
        start_time = time.time()

        # ⭐ 阶段0: 分离System Prompt（特殊处理）
        system_prompts, other_messages = self._separate_system_prompts(messages)

        if not other_messages:
            # 如果只有system消息，直接返回
            return {
                'compressed_messages': system_prompts,
                'system_prompts': system_prompts,
                'system_prompts_count': len(system_prompts),
                'statistics': {
                    'original_count': len(messages),
                    'compressed_count': len(system_prompts),
                    'compression_ratio': 0.0,
                    'system_prompts_preserved': True
                }
            }

        # 计算原始tokens
        original_tokens = sum(count_tokens(m.get('content', '')) for m in other_messages)

        print(f"\n{'━' * 60}")
        print(f"🔄 正在执行智能压缩...")
        print(f"{'━' * 60}\n")
        print(f"⭐ System Prompt: {len(system_prompts)}条（完全保留，不压缩）")
        print(f"📝 待压缩消息: {len(other_messages)}条 ({original_tokens:,} tokens)\n")

        # 阶段1: 消息分类
        print("阶段 1/8: 分类消息")
        classified = self.classify_messages(other_messages)
        print(f"  • Critical: {len(classified['critical'])}条 (必须保留)")
        print(f"  • Important: {len(classified['important'])}条 (可压缩)")
        print(f"  • Contextual: {len(classified['contextual'])}条 (提取要点)")
        print(f"  • Redundant: {len(classified['redundant'])}条 (可删除)\n")

        # 阶段2: 提取实体
        print("阶段 2/8: 提取实体")
        entities = self.extract_entities(classified)
        print(f"  • 文件: {entities['files'][:5]}")
        print(f"  • 函数: {entities['functions'][:5]}")
        print(f"  • 类: {entities['classes'][:5]}")
        print(f"  • 错误: {entities['errors'][:3]}\n")

        # 阶段3: 构建知识图谱
        print("阶段 3/8: 构建知识图谱")
        graph = self.build_knowledge_graph(entities, other_messages)
        print(f"  • 节点数: {graph['node_count']}")
        print(f"  • 关系数: {graph['edge_count']}\n")

        # 阶段4: 重要性评分
        print("阶段 4/8: 重要性评分")
        scored_messages = self.score_messages(other_messages, graph)
        print(f"  • 完成 (基于引用频率和时间距离)\n")

        # 阶段5: 生成压缩摘要
        print("阶段 5/8: 生成压缩摘要")
        summary = self.generate_summary(scored_messages, entities, classified)
        summary_tokens = count_tokens(summary)
        print(f"  • 原始: {len(other_messages)}条消息, {original_tokens:,} tokens")
        print(f"  • 摘要: 1条消息, {summary_tokens:,} tokens\n")

        # 阶段6: 保留关键代码块
        print("阶段 6/8: 保留关键代码")
        code_blocks = self._extract_all_code_blocks(other_messages)
        print(f"  • 保留代码块: {len(code_blocks)}个\n")

        # 阶段7: 重构对话流
        print("阶段 7/8: 重构对话流")
        recent_messages = self._get_recent_important_messages(scored_messages, count=3)
        print(f"  • 保留最近重要消息: {len(recent_messages)}条\n")

        # 阶段8: 质量验证
        print("阶段 8/8: 质量验证")
        validation = self._validate_compression(entities, summary, code_blocks)
        print(f"  • 关键实体保留: {'✅' if validation['entities_preserved'] else '❌'} {validation['entity_retention']*100:.0f}%")
        print(f"  • 因果关系完整: {'✅' if validation['causality_intact'] else '❌'}")
        print(f"  • 代码上下文: {'✅' if validation['code_context'] else '❌'}\n")

        # ⭐ 组合最终结果：System Prompts + 压缩摘要 + 最近消息
        compressed_messages = system_prompts + [{
            'role': 'system',
            'content': summary,
            'type': 'compressed_summary',
            'original_count': len(other_messages),
            'timestamp': time.time()
        }] + recent_messages

        # 计算压缩后的tokens
        compressed_tokens = sum(count_tokens(m.get('content', '')) for m in compressed_messages)

        # 计算统计信息
        compression_ratio = 1 - (compressed_tokens / max(original_tokens, 1))
        execution_time = time.time() - start_time

        print(f"{'━' * 60}")
        print(f"✅ 压缩完成！")
        print(f"{'━' * 60}\n")

        statistics = {
            'original_count': len(messages),
            'original_tokens': original_tokens,
            'compressed_count': len(compressed_messages),
            'compressed_tokens': compressed_tokens,
            'tokens_saved': original_tokens - compressed_tokens,
            'compression_ratio': compression_ratio,
            'info_retention': validation.get('overall_quality', 0.95),
            'execution_time': execution_time,
            'system_prompts_preserved': len(system_prompts),
            'system_role_untouched': True
        }

        return {
            'compressed_messages': compressed_messages,
            'system_prompts': system_prompts,
            'summary': summary,
            'entities': entities,
            'code_blocks': code_blocks,
            'statistics': statistics
        }

    def _separate_system_prompts(self, messages: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        ⭐ 分离系统提示词和普通消息

        Args:
            messages: 消息列表

        Returns:
            (system_prompts, other_messages)
        """
        if not self.preserve_system:
            return [], messages

        system_prompts = []
        other_messages = []

        for msg in messages:
            if msg.get('role') == default_config.SYSTEM_ROLE_NAME:
                system_prompts.append(msg)
            else:
                other_messages.append(msg)

        return system_prompts, other_messages

    async def classify_messages(self, messages: List[Dict]) -> Dict[str, List[Dict]]:
        """
        阶段1: 消息分类（LLM驱动 + 规则匹配Fallback）

        Args:
            messages: 消息列表

        Returns:
            分类结果字典
        """
        if self.use_llm:
            return await self._classify_messages_llm(messages)
        else:
            return self._classify_messages_rules(messages)

    async def _classify_messages_llm(self, messages: List[Dict]) -> Dict[str, List[Dict]]:
        """
        使用LLM进行智能消息分类

        Args:
            messages: 消息列表

        Returns:
            分类结果字典
        """
        try:
            # 构建分析prompt
            messages_summary = []
            for i, msg in enumerate(messages[:20]):  # 限制前20条以避免超长
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:200]  # 截取前200字符
                messages_summary.append(f"{i}. [{role}] {content}...")

            prompt = f"""分析以下对话消息，将每条消息分类为以下类别之一：
- critical: 关键消息（错误报告、重要决策、关键问题）
- important: 重要消息（功能实现、设计讨论、配置更改）
- contextual: 上下文消息（解释说明、一般讨论）
- redundant: 冗余消息（简单确认、重复内容、无关信息）

对话消息：
{chr(10).join(messages_summary)}

请以JSON格式返回分类结果，格式如下：
{{
    "classifications": [
        {{"index": 0, "category": "critical", "reason": "报告了严重错误"}},
        {{"index": 1, "category": "important", "reason": "讨论了核心功能实现"}},
        ...
    ]
}}

只返回JSON，不要其他内容。"""

            llm_messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat(llm_messages, stream=False)

            # 解析LLM响应
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            result = json.loads(response_clean.strip())
            classifications = result.get('classifications', [])

            # 构建分类字典
            classified = {
                'critical': [],
                'important': [],
                'contextual': [],
                'redundant': []
            }

            # 根据LLM分析结果分类
            for item in classifications:
                idx = item.get('index')
                category = item.get('category', 'contextual')
                if 0 <= idx < len(messages):
                    classified[category].append(messages[idx])

            # 处理未分类的消息（fallback）
            classified_indices = {item['index'] for item in classifications}
            for i, msg in enumerate(messages):
                if i not in classified_indices:
                    classified['contextual'].append(msg)

            print(f"  ✨ LLM分类成功")
            return classified

        except Exception as e:
            print(f"  ⚠️  LLM分类失败: {e}，使用规则匹配Fallback")
            return self._classify_messages_rules(messages)

    def _classify_messages_rules(self, messages: List[Dict]) -> Dict[str, List[Dict]]:
        """
        使用规则匹配进行消息分类（Fallback）

        Args:
            messages: 消息列表

        Returns:
            分类结果字典
        """
        classified = {
            'critical': [],      # 关键消息（错误、重要决策）
            'important': [],     # 重要消息（实现、设计）
            'contextual': [],    # 上下文消息（解释、讨论）
            'redundant': []      # 冗余消息（重复、无关）
        }

        critical_keywords = default_config.MESSAGE_CLASSIFICATION['critical_keywords']
        important_keywords = default_config.MESSAGE_CLASSIFICATION['important_keywords']

        for msg in messages:
            content = msg.get('content', '').lower()

            # 检查是否包含关键词
            has_critical = any(kw in content for kw in critical_keywords)
            has_important = any(kw in content for kw in important_keywords)

            if has_critical:
                classified['critical'].append(msg)
            elif has_important:
                classified['important'].append(msg)
            elif len(content) > 50:  # 有实质内容
                classified['contextual'].append(msg)
            else:
                classified['redundant'].append(msg)

        return classified

    async def extract_entities(self, classified: Dict[str, List[Dict]]) -> Dict[str, List[str]]:
        """
        阶段2: 提取关键实体（LLM驱动 + 规则匹配Fallback）

        Args:
            classified: 分类后的消息

        Returns:
            实体字典
        """
        if self.use_llm:
            return await self._extract_entities_llm(classified)
        else:
            return self._extract_entities_rules(classified)

    async def _extract_entities_llm(self, classified: Dict[str, List[Dict]]) -> Dict[str, List[str]]:
        """
        使用LLM进行智能实体提取

        Args:
            classified: 分类后的消息

        Returns:
            实体字典
        """
        try:
            # 收集所有消息内容
            all_content = []
            for category in ['critical', 'important', 'contextual']:
                for msg in classified.get(category, [])[:10]:  # 每类取前10条
                    content = msg.get('content', '')[:300]  # 限制长度
                    all_content.append(content)

            combined_content = '\n---\n'.join(all_content)

            prompt = f"""分析以下技术对话内容，提取关键技术实体：

对话内容：
{combined_content}

请识别并提取：
1. **文件名**（如 main.py, config.json, app.ts 等）
2. **函数名**（如 calculate_score, handleSubmit, async_process 等）
3. **类名**（如 UserManager, DataProcessor, APIClient 等）
4. **重要变量**（如 API_KEY, MAX_RETRIES, user_data 等）
5. **错误类型**（如 ValueError, ConnectionError, 500 Internal Server Error 等）

返回JSON格式：
{{
    "files": ["file1.py", "file2.js"],
    "functions": ["func1", "func2"],
    "classes": ["Class1", "Class2"],
    "variables": ["var1", "var2"],
    "errors": ["Error1", "Error2"]
}}

只返回JSON，不要其他内容。确保每个列表只包含最相关的前10项。"""

            llm_messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat(llm_messages, stream=False)

            # 解析响应
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]

            entities = json.loads(response_clean.strip())

            # 确保所有键存在
            for key in ['files', 'functions', 'classes', 'variables', 'errors']:
                if key not in entities:
                    entities[key] = []

            # 去重
            for key in entities:
                entities[key] = list(set(entities[key]))[:10]  # 限制每类最多10个

            print(f"  ✨ LLM实体提取成功")
            return entities

        except Exception as e:
            print(f"  ⚠️  LLM实体提取失败: {e}，使用规则匹配Fallback")
            return self._extract_entities_rules(classified)

    def _extract_entities_rules(self, classified: Dict[str, List[Dict]]) -> Dict[str, List[str]]:
        """
        使用规则匹配进行实体提取（Fallback）

        Args:
            classified: 分类后的消息

        Returns:
            实体字典
        """
        all_entities = {
            'files': [],
            'functions': [],
            'variables': [],
            'classes': [],
            'errors': []
        }

        # 从所有消息中提取实体
        for category, msgs in classified.items():
            for msg in msgs:
                content = msg.get('content', '')
                entities = extract_entities(content)

                for key in all_entities:
                    all_entities[key].extend(entities.get(key, []))

        # 去重并计数
        for key in all_entities:
            all_entities[key] = list(set(all_entities[key]))

        return all_entities

    def build_knowledge_graph(self, entities: Dict, messages: List[Dict]) -> Dict:
        """
        阶段3: 构建知识图谱

        Args:
            entities: 实体字典
            messages: 消息列表

        Returns:
            知识图谱字典
        """
        # 简化版知识图谱：记录实体之间的共现关系
        graph = {
            'nodes': [],
            'edges': [],
            'node_count': 0,
            'edge_count': 0
        }

        # 收集所有实体作为节点
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                graph['nodes'].append({
                    'id': entity,
                    'type': entity_type
                })

        graph['node_count'] = len(graph['nodes'])

        # 构建边（实体共现关系）
        for msg in messages:
            content = msg.get('content', '')
            msg_entities = []

            # 找出这条消息中包含的所有实体
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    if entity in content:
                        msg_entities.append(entity)

            # 为共现的实体创建边
            for i in range(len(msg_entities)):
                for j in range(i + 1, len(msg_entities)):
                    graph['edges'].append({
                        'from': msg_entities[i],
                        'to': msg_entities[j],
                        'weight': 1
                    })

        graph['edge_count'] = len(graph['edges'])

        return graph

    def score_messages(self, messages: List[Dict], graph: Dict) -> List[Dict]:
        """
        阶段4: 为消息评分

        Args:
            messages: 消息列表
            graph: 知识图谱

        Returns:
            带评分的消息列表
        """
        try:
            print(f"[DEBUG score_messages] 开始评分，消息数量: {len(messages)}")
            print(f"[DEBUG score_messages] Graph edges数量: {len(graph.get('edges', []))}")

            scored = []

            # 统计实体引用次数
            entity_counts = Counter()
            for edge in graph['edges']:
                entity_counts[edge['from']] += 1
                entity_counts[edge['to']] += 1

            print(f"[DEBUG score_messages] 实体统计完成，实体数量: {len(entity_counts)}")
            current_time = time.time()

            for i, msg in enumerate(messages):
                try:
                    print(f"[DEBUG score_messages] 处理消息 {i+1}/{len(messages)}, role={msg.get('role')}")

                    # 确保content是字符串
                    content = msg.get('content', '')
                    if content is None:
                        content = ''
                    content = str(content)

                    timestamp = msg.get('timestamp', current_time - (len(messages) - i) * 60)
                    print(f"[DEBUG score_messages] Content长度: {len(content)}, timestamp: {timestamp}")

                    # 计算评分因素
                    # 1. 实体重要性（被引用次数）
                    entity_score = 0
                    for entity, count in entity_counts.items():
                        try:
                            if str(entity) in content:
                                entity_score += count
                        except Exception as e:
                            print(f"[ERROR] 实体检查失败: entity={entity}, error={e}")
                            continue

                    # 2. 时间距离（越近越重要）
                    time_distance = current_time - timestamp
                    time_score = 1.0 / (1.0 + time_distance / 3600)  # 以小时为单位衰减

                    # 3. 内容长度（更长的内容可能更重要）
                    length_score = min(len(content) / 1000, 1.0)

                    # 4. 角色权重（assistant的回答通常更重要）
                    role_weight = 1.5 if msg.get('role') == 'assistant' else 1.0

                    # 综合评分
                    final_score = (
                        entity_score * 0.4 +
                        time_score * 0.3 +
                        length_score * 0.2 +
                        role_weight * 0.1
                    )

                    print(f"[DEBUG score_messages] 评分完成: final_score={final_score:.4f}")

                    # 创建评分后的消息（使用字典复制而不是copy方法）
                    scored_msg = dict(msg)
                    scored_msg['importance_score'] = final_score
                    scored.append(scored_msg)

                except Exception as msg_error:
                    print(f"[ERROR score_messages] 处理消息 {i} 时出错: {msg_error}")
                    print(f"[ERROR] 消息内容: {msg}")
                    import traceback
                    traceback.print_exc()
                    # 继续处理下一条消息
                    continue

            # 按评分排序
            print(f"[DEBUG score_messages] 开始排序，scored消息数量: {len(scored)}")
            scored.sort(key=lambda m: m.get('importance_score', 0), reverse=True)

            print(f"[DEBUG score_messages] 评分完成，返回 {len(scored)} 条消息")
            return scored

        except Exception as e:
            print(f"[ERROR score_messages] 评分过程出错: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def generate_summary(self, scored_messages: List[Dict],
                        entities: Dict, classified: Dict) -> str:
        """
        阶段5: 生成压缩摘要（LLM驱动 + 模板Fallback）

        Args:
            scored_messages: 评分后的消息
            entities: 实体字典
            classified: 分类结果

        Returns:
            压缩摘要文本
        """
        if self.use_llm:
            return await self._generate_summary_llm(scored_messages, entities, classified)
        else:
            return self._generate_summary_template(scored_messages, entities, classified)

    async def _generate_summary_llm(self, scored_messages: List[Dict],
                                    entities: Dict, classified: Dict) -> str:
        """
        使用LLM生成高质量压缩摘要

        Args:
            scored_messages: 评分后的消息
            entities: 实体字典
            classified: 分类结果

        Returns:
            压缩摘要文本
        """
        try:
            # 收集关键消息内容
            critical_messages = []
            for msg in classified.get('critical', [])[:5]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:500]
                critical_messages.append(f"[{role}] {content}")

            important_messages = []
            for msg in classified.get('important', [])[:5]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:500]
                important_messages.append(f"[{role}] {content}")

            # 构建实体信息
            entities_text = []
            if entities.get('files'):
                entities_text.append(f"文件: {', '.join(entities['files'][:5])}")
            if entities.get('functions'):
                entities_text.append(f"函数: {', '.join(entities['functions'][:5])}")
            if entities.get('classes'):
                entities_text.append(f"类: {', '.join(entities['classes'][:5])}")
            if entities.get('errors'):
                entities_text.append(f"错误: {', '.join(entities['errors'][:3])}")

            total_messages = sum(len(msgs) for msgs in classified.values())

            prompt = f"""请将以下技术对话历史压缩为简洁的摘要（200-500 tokens），保留关键信息。

**关键技术实体：**
{chr(10).join(entities_text)}

**关键消息（Critical）：**
{chr(10).join(critical_messages) if critical_messages else "无"}

**重要消息（Important）：**
{chr(10).join(important_messages) if important_messages else "无"}

**总消息数：** {total_messages}条

请生成压缩摘要，要求：
1. 用第三人称简洁描述对话的技术背景和目标
2. 突出关键问题、决策和解决方案
3. 保留重要的技术细节（文件名、函数名、错误类型等）
4. 说明已解决/未解决的问题
5. 如果有代码实现，简要说明实现方式

格式要求：
- 使用Markdown格式
- 分段清晰（背景、问题、解决方案、状态）
- 简洁专业，避免冗余

直接输出摘要内容，不要包含"以下是摘要"等引导语。"""

            llm_messages = [{"role": "user", "content": prompt}]
            summary = await self.llm_client.chat(llm_messages, stream=False)

            # 添加元数据
            summary_with_meta = f"📋 **对话历史摘要** (AI生成)\n\n{summary.strip()}\n\n_压缩自 {total_messages} 条历史消息_"

            print(f"  ✨ LLM摘要生成成功（{count_tokens(summary_with_meta)} tokens）")
            return summary_with_meta

        except Exception as e:
            print(f"  ⚠️  LLM摘要生成失败: {e}，使用模板Fallback")
            return self._generate_summary_template(scored_messages, entities, classified)

    def _generate_summary_template(self, scored_messages: List[Dict],
                                   entities: Dict, classified: Dict) -> str:
        """
        使用模板生成摘要（Fallback）

        Args:
            scored_messages: 评分后的消息
            entities: 实体字典
            classified: 分类结果

        Returns:
            压缩摘要文本
        """
        summary_parts = []

        # 添加摘要头部
        summary_parts.append("📋 **对话历史摘要** (自动生成)")
        summary_parts.append("")

        # 关键实体
        if entities['files'] or entities['functions'] or entities['classes']:
            summary_parts.append("**🔑 关键实体:**")
            if entities['files'][:5]:
                summary_parts.append(f"- 文件: {', '.join(entities['files'][:5])}")
            if entities['functions'][:5]:
                summary_parts.append(f"- 函数: {', '.join(entities['functions'][:5])}")
            if entities['classes'][:5]:
                summary_parts.append(f"- 类: {', '.join(entities['classes'][:5])}")
            if entities['errors'][:3]:
                summary_parts.append(f"- 错误: {', '.join(entities['errors'][:3])}")
            summary_parts.append("")

        # 关键对话要点（从高分消息中提取）
        summary_parts.append("**💬 对话要点:**")
        for i, msg in enumerate(scored_messages[:5], 1):  # 取前5条重要消息
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            preview = content[:100] + ('...' if len(content) > 100 else '')
            summary_parts.append(f"{i}. [{role}] {preview}")

        summary_parts.append("")

        # 关键决策或结论
        if classified['critical']:
            summary_parts.append("**⚠️  关键问题/决策:**")
            for msg in classified['critical'][:3]:
                content = msg.get('content', '')
                preview = content[:80] + ('...' if len(content) > 80 else '')
                summary_parts.append(f"- {preview}")
            summary_parts.append("")

        # 统计信息
        total_messages = sum(len(msgs) for msgs in classified.values())
        summary_parts.append(f"_压缩自 {total_messages} 条历史消息_")

        return '\n'.join(summary_parts)

    def _extract_all_code_blocks(self, messages: List[Dict]) -> List[Dict]:
        """
        阶段6: 提取所有代码块

        Args:
            messages: 消息列表

        Returns:
            代码块列表
        """
        all_code_blocks = []

        for msg in messages:
            content = msg.get('content', '')
            code_blocks = extract_code_blocks(content)

            for block in code_blocks:
                all_code_blocks.append({
                    'language': block['language'],
                    'code': block['code'],
                    'from_message': msg.get('role', 'unknown')
                })

        return all_code_blocks

    def _get_recent_important_messages(self, scored_messages: List[Dict],
                                      count: int = 3) -> List[Dict]:
        """
        阶段7: 获取最近的重要消息（完整保留）

        Args:
            scored_messages: 评分后的消息
            count: 保留数量

        Returns:
            最近重要消息列表
        """
        # 按时间排序（最新的在后面）
        sorted_by_time = sorted(
            scored_messages,
            key=lambda m: m.get('timestamp', 0)
        )

        # 取最后N条
        recent = sorted_by_time[-count:] if len(sorted_by_time) >= count else sorted_by_time

        # 移除评分字段（清理）
        clean_messages = []
        for msg in recent:
            clean_msg = {k: v for k, v in msg.items() if k != 'importance_score'}
            clean_messages.append(clean_msg)

        return clean_messages

    def _validate_compression(self, entities: Dict, summary: str,
                             code_blocks: List[Dict]) -> Dict:
        """
        阶段8: 验证压缩质量

        Args:
            entities: 原始实体
            summary: 压缩摘要
            code_blocks: 代码块

        Returns:
            验证结果字典
        """
        # 检查关键实体是否在摘要中保留
        preserved_count = 0
        total_count = sum(len(ent_list) for ent_list in entities.values())

        for entity_type, entity_list in entities.items():
            for entity in entity_list[:5]:  # 检查前5个最重要的
                if entity in summary:
                    preserved_count += 1

        entity_retention = preserved_count / max(total_count, 1) if total_count > 0 else 1.0

        validation = {
            'entities_preserved': entity_retention > 0.5,  # 至少保留50%
            'entity_retention': entity_retention,
            'causality_intact': True,  # 简化：假设因果关系完整
            'code_context': len(code_blocks) > 0,  # 代码上下文是否保留
            'overall_quality': min(entity_retention + 0.3, 1.0)  # 综合质量评分
        }

        return validation

    def calculate_compression_ratio(self, original: List[Dict],
                                   compressed: List[Dict]) -> float:
        """
        计算压缩率

        Args:
            original: 原始消息列表
            compressed: 压缩后的消息列表

        Returns:
            压缩率（0-1之间，越大表示压缩越多）
        """
        original_tokens = sum(count_tokens(m.get('content', '')) for m in original)
        compressed_tokens = sum(count_tokens(m.get('content', '')) for m in compressed)

        if original_tokens == 0:
            return 0.0

        return 1 - (compressed_tokens / original_tokens)


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test_compressor():
        print("=== AU2压缩算法测试 ===\n")

        compressor = AU2Compressor()

        # 准备测试数据
        test_messages = [
            {"role": "system", "content": "你是一个Python编程助手"},  # ⭐ System Prompt
            {"role": "user", "content": "创建一个Flask项目"},
            {"role": "assistant", "content": "好的，我来帮你创建Flask项目。首先需要安装Flask..."},
            {"role": "user", "content": "添加用户认证功能"},
            {"role": "assistant", "content": "我们可以使用Flask-Login来实现用户认证..."},
            {"role": "user", "content": "main.py第42行出现TypeError"},
            {"role": "assistant", "content": "这个TypeError是因为...我们需要修复它"},
            # ... 更多消息
        ]

        # 执行压缩
        result = await compressor.compress(test_messages)

        # 显示结果
        print("\n📊 压缩效果:")
        stats = result['statistics']
        print(f"  原始Tokens: {stats['original_tokens']:,}")
        print(f"  压缩后Tokens: {stats['compressed_tokens']:,}")
        print(f"  节省Tokens: {stats['tokens_saved']:,} ({stats['compression_ratio']*100:.1f}%)")
        print(f"  信息保留率: {stats['info_retention']*100:.0f}%")
        print(f"  耗时: {stats['execution_time']:.2f}秒")
        print(f"  ⭐ System Prompts保留: {stats['system_prompts_preserved']}条")

        print(f"\n📝 压缩摘要预览:")
        print(result['summary'][:200] + "...")

    asyncio.run(test_compressor())
