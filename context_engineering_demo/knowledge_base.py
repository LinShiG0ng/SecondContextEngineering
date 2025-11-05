"""
长期知识库管理
持久化存储项目元数据、决策记录、代码片段
"""

import json
import time
from typing import List, Dict, Optional
from pathlib import Path


class KnowledgeBase:
    """长期知识库"""

    def __init__(self, kb_path: Optional[str] = None):
        """
        初始化知识库

        Args:
            kb_path: 知识库文件路径
        """
        self.kb_path = Path(kb_path or "./workspace/knowledge.json")

        # 创建目录
        self.kb_path.parent.mkdir(parents=True, exist_ok=True)

        # 加载现有知识库
        self.data = self.load()

    def load(self) -> Dict:
        """
        加载知识库

        Returns:
            知识库数据
        """
        if not self.kb_path.exists():
            return self._create_empty_kb()

        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载知识库失败: {e}")
            return self._create_empty_kb()

    def _create_empty_kb(self) -> Dict:
        """创建空知识库结构"""
        return {
            'version': '1.0',
            'created_at': time.time(),
            'last_updated': None,
            'project_metadata': {},
            'decisions': [],
            'code_snippets': [],
            'entities': {},
            'conversations': []
        }

    def save(self, data: Optional[Dict] = None):
        """
        保存知识库

        Args:
            data: 要保存的数据（可选，默认使用self.data）
        """
        if data:
            self.data = data

        self.data['last_updated'] = time.time()

        try:
            with open(self.kb_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 保存知识库失败: {e}")

    def update(self, new_info: Dict):
        """
        增量更新知识库

        Args:
            new_info: 新信息字典，可包含：
                - project_metadata: 项目元数据
                - decisions: 决策记录
                - code_snippets: 代码片段
                - entities: 实体信息
        """
        # 更新项目元数据
        if 'project_metadata' in new_info:
            self.data['project_metadata'].update(new_info['project_metadata'])

        # 添加决策记录
        if 'decisions' in new_info:
            for decision in new_info['decisions']:
                self.data['decisions'].append({
                    'timestamp': time.time(),
                    'decision': decision
                })

        # 添加代码片段
        if 'code_snippets' in new_info:
            for snippet in new_info['code_snippets']:
                self.data['code_snippets'].append({
                    'timestamp': time.time(),
                    'snippet': snippet
                })

        # 更新实体
        if 'entities' in new_info:
            for entity_type, entities in new_info['entities'].items():
                if entity_type not in self.data['entities']:
                    self.data['entities'][entity_type] = []
                self.data['entities'][entity_type].extend(entities)
                # 去重
                self.data['entities'][entity_type] = list(set(self.data['entities'][entity_type]))

        # 保存更新
        self.save()

    def query(self, keywords: List[str]) -> List[Dict]:
        """
        按关键词搜索知识库

        Args:
            keywords: 关键词列表

        Returns:
            匹配的条目列表
        """
        results = []

        # 搜索决策记录
        for decision in self.data.get('decisions', []):
            decision_text = str(decision.get('decision', '')).lower()
            if any(kw.lower() in decision_text for kw in keywords):
                results.append({
                    'type': 'decision',
                    'content': decision,
                    'timestamp': decision.get('timestamp')
                })

        # 搜索代码片段
        for snippet in self.data.get('code_snippets', []):
            snippet_text = str(snippet.get('snippet', '')).lower()
            if any(kw.lower() in snippet_text for kw in keywords):
                results.append({
                    'type': 'code_snippet',
                    'content': snippet,
                    'timestamp': snippet.get('timestamp')
                })

        # 搜索实体
        for entity_type, entities in self.data.get('entities', {}).items():
            for entity in entities:
                if any(kw.lower() in entity.lower() for kw in keywords):
                    results.append({
                        'type': 'entity',
                        'entity_type': entity_type,
                        'content': entity
                    })

        return results

    def to_context_message(self) -> Dict:
        """
        将知识库转换为上下文消息格式

        Returns:
            消息字典
        """
        # 构建知识库摘要
        summary_parts = []

        summary_parts.append("📚 **项目知识库**")
        summary_parts.append("")

        # 项目元数据
        if self.data.get('project_metadata'):
            summary_parts.append("**项目信息:**")
            for key, value in self.data['project_metadata'].items():
                summary_parts.append(f"- {key}: {value}")
            summary_parts.append("")

        # 关键决策
        if self.data.get('decisions'):
            summary_parts.append("**关键决策:**")
            for decision in self.data['decisions'][-5:]:  # 最近5条
                summary_parts.append(f"- {decision.get('decision')}")
            summary_parts.append("")

        # 实体统计
        if self.data.get('entities'):
            summary_parts.append("**已识别实体:**")
            for entity_type, entities in self.data['entities'].items():
                if entities:
                    summary_parts.append(f"- {entity_type}: {', '.join(entities[:5])}")
            summary_parts.append("")

        return {
            'role': 'system',
            'content': '\n'.join(summary_parts),
            'type': 'knowledge_base',
            'timestamp': time.time()
        }

    def get_statistics(self) -> Dict:
        """
        获取知识库统计信息

        Returns:
            统计信息字典
        """
        return {
            'total_decisions': len(self.data.get('decisions', [])),
            'total_code_snippets': len(self.data.get('code_snippets', [])),
            'total_entity_types': len(self.data.get('entities', {})),
            'total_entities': sum(len(entities) for entities in self.data.get('entities', {}).values()),
            'last_updated': self.data.get('last_updated'),
            'kb_exists': self.kb_path.exists()
        }


if __name__ == "__main__":
    # 测试代码
    print("=== 知识库管理测试 ===\n")

    kb = KnowledgeBase("./workspace/test_knowledge.json")

    # 测试更新
    print("1. 更新知识库...")
    kb.update({
        'project_metadata': {
            'name': 'Context Engineering Demo',
            'language': 'Python',
            'framework': 'FastAPI'
        },
        'decisions': [
            '使用三层存储架构',
            '支持多种LLM API'
        ],
        'entities': {
            'files': ['main.py', 'config.py'],
            'functions': ['compress', 'inject_context']
        }
    })
    print("   ✅ 更新完成\n")

    # 测试查询
    print("2. 查询知识库...")
    results = kb.query(['compress', 'storage'])
    print(f"   找到 {len(results)} 条相关记录\n")

    # 测试转换为上下文
    print("3. 转换为上下文消息...")
    context_msg = kb.to_context_message()
    print(f"   消息预览:\n{context_msg['content'][:200]}...\n")

    # 统计信息
    print("4. 知识库统计:")
    stats = kb.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
