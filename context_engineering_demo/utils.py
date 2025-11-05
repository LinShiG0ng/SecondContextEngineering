"""
工具函数模块
提供token计数、实体提取、格式化等辅助功能
"""

import re
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def count_tokens(text: str) -> int:
    """
    计算文本的token数量

    使用简化算法：中文字符按1.5个token计算，英文按4字符1token计算
    这是一个近似值，实际应使用tiktoken库

    Args:
        text: 要计算的文本

    Returns:
        估算的token数量
    """
    if not text:
        return 0

    # 统计中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计其他字符
    other_chars = len(text) - chinese_chars

    # 中文字符按1.5个token，英文按4字符1token
    tokens = int(chinese_chars * 1.5 + other_chars / 4)

    return max(tokens, 1)  # 至少1个token


def count_tokens_tiktoken(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    使用tiktoken库精确计算token数量（如果可用）

    Args:
        text: 要计算的文本
        model: 模型名称

    Returns:
        精确的token数量
    """
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except ImportError:
        # tiktoken未安装，使用简化算法
        return count_tokens(text)
    except Exception:
        # 其他错误，使用简化算法
        return count_tokens(text)


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    提取文本中的代码块

    Args:
        text: 包含代码块的文本

    Returns:
        代码块列表，每个元素包含language和code
    """
    # 匹配markdown代码块格式 ```language\ncode\n```
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)

    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            'language': language or 'text',
            'code': code.strip()
        })

    return code_blocks


def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    提取文本中的关键实体

    使用正则表达式识别：
    - 文件名（.py, .js, .json等）
    - 函数名（def xxx, function xxx, async def xxx）
    - 变量名（var/let/const xxx, xxx = ）
    - 类名（class Xxx）
    - 错误信息（Error, Exception）

    Args:
        text: 要分析的文本

    Returns:
        实体字典，包含files, functions, variables, classes, errors
    """
    entities = {
        'files': [],
        'functions': [],
        'variables': [],
        'classes': [],
        'errors': []
    }

    # 文件名（常见扩展名）
    file_pattern = r'\b[\w/\-\.]+\.(?:py|js|ts|jsx|tsx|json|yaml|yml|md|txt|csv|html|css|java|cpp|go|rs|rb)\b'
    entities['files'] = list(set(re.findall(file_pattern, text)))

    # 函数名
    function_patterns = [
        r'def\s+(\w+)\s*\(',           # Python def
        r'async\s+def\s+(\w+)\s*\(',  # Python async def
        r'function\s+(\w+)\s*\(',      # JavaScript function
        r'const\s+(\w+)\s*=\s*\(',     # Arrow function
        r'(\w+)\s*\([^)]*\)\s*{',      # General function
    ]
    for pattern in function_patterns:
        entities['functions'].extend(re.findall(pattern, text))
    entities['functions'] = list(set(entities['functions']))

    # 类名
    class_patterns = [
        r'class\s+(\w+)',              # Python/JavaScript class
        r'interface\s+(\w+)',          # TypeScript interface
    ]
    for pattern in class_patterns:
        entities['classes'].extend(re.findall(pattern, text))
    entities['classes'] = list(set(entities['classes']))

    # 错误信息
    error_pattern = r'(\w*(?:Error|Exception))\b'
    entities['errors'] = list(set(re.findall(error_pattern, text)))

    return entities


def format_message(role: str, content: str, timestamp: Optional[float] = None,
                   tokens: Optional[int] = None) -> Dict:
    """
    格式化消息为标准格式

    Args:
        role: 消息角色（user/assistant/system）
        content: 消息内容
        timestamp: 时间戳（可选）
        tokens: token数量（可选）

    Returns:
        格式化的消息字典
    """
    message = {
        'role': role,
        'content': content,
        'timestamp': timestamp or time.time(),
    }

    if tokens is not None:
        message['tokens'] = tokens
    else:
        message['tokens'] = count_tokens(content)

    return message


def print_colored(text: str, color: str = 'white', bold: bool = False):
    """
    打印彩色文本（使用ANSI转义码）

    Args:
        text: 要打印的文本
        color: 颜色（red/green/yellow/blue/magenta/cyan/white）
        bold: 是否加粗
    """
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'reset': '\033[0m',
    }

    bold_code = '\033[1m' if bold else ''
    color_code = colors.get(color, colors['white'])
    reset_code = colors['reset']

    print(f"{bold_code}{color_code}{text}{reset_code}")


def print_box(text: str, width: int = 60, char: str = '━'):
    """
    打印文本框

    Args:
        text: 要显示的文本
        width: 框的宽度
        char: 边框字符
    """
    print(char * width)
    print(text.center(width))
    print(char * width)


def print_progress_bar(percentage: float, width: int = 40,
                       filled_char: str = '▓', empty_char: str = '░'):
    """
    打印进度条

    Args:
        percentage: 百分比（0-1）
        width: 进度条宽度
        filled_char: 填充字符
        empty_char: 空字符
    """
    filled = int(width * percentage)
    empty = width - filled
    bar = filled_char * filled + empty_char * empty

    # 根据百分比选择颜色
    if percentage < 0.6:
        color = 'green'
        status = '✅ 正常'
    elif percentage < 0.8:
        color = 'yellow'
        status = '⚠️  警告'
    elif percentage < 0.92:
        color = 'red'
        status = '⚠️  警告'
    else:
        color = 'magenta'
        status = '🔄 触发压缩'

    print_colored(f"[Token使用率: {percentage*100:.0f}% {bar}] {status}", color)


def print_statistics(stats: Dict):
    """
    打印统计信息

    Args:
        stats: 统计数据字典
    """
    print_box('📊 系统统计信息')
    print()

    # 对话统计
    if 'conversation' in stats:
        conv = stats['conversation']
        print_colored("💬 对话统计:", 'cyan', bold=True)
        print(f"  • 总消息数: {conv.get('total_messages', 0)}条")
        print(f"  • 用户消息: {conv.get('user_messages', 0)}条")
        print(f"  • 助手消息: {conv.get('assistant_messages', 0)}条")
        print(f"  • 当前Token使用: {conv.get('current_tokens', 0):,} / {conv.get('max_tokens', 0):,} ({conv.get('usage_percentage', 0)*100:.0f}%)")
        print()

    # 压缩统计
    if 'compression' in stats:
        comp = stats['compression']
        print_colored("🔄 压缩统计:", 'yellow', bold=True)
        print(f"  • 压缩次数: {comp.get('count', 0)}次")
        print(f"  • 总节省Tokens: {comp.get('total_saved', 0):,}")
        print(f"  • 平均压缩率: {comp.get('avg_ratio', 0)*100:.1f}%")
        print(f"  • 信息保留率: {comp.get('retention_rate', 0)*100:.0f}%")
        print()

    # 存储结构
    if 'storage' in stats:
        store = stats['storage']
        print_colored("🏗️  存储结构:", 'blue', bold=True)
        print(f"  • 短期记忆: {store.get('short_term_count', 0)}条消息 ({store.get('short_term_tokens', 0):,} tokens)")
        print(f"  • 中期记忆: {store.get('mid_term_count', 0)}条消息 ({store.get('mid_term_tokens', 0):,} tokens)")
        print(f"  • 长期知识库: {'已保存' if store.get('long_term_saved', False) else '未保存'}")
        print()

    # API统计
    if 'api' in stats:
        api = stats['api']
        print_colored("📡 API统计:", 'green', bold=True)
        print(f"  • 总请求次数: {api.get('total_requests', 0)}次")
        print(f"  • 平均响应时间: {api.get('avg_response_time', 0):.2f}秒")
        print(f"  • 预估总成本: ${api.get('estimated_cost', 0):.4f}")
        print()

    print_box('', char='━')


def format_timestamp(timestamp: float) -> str:
    """
    格式化时间戳

    Args:
        timestamp: Unix时间戳

    Returns:
        格式化的时间字符串
    """
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断文本

    Args:
        text: 要截断的文本
        max_length: 最大长度
        suffix: 后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def estimate_cost(tokens: int, model: str = "gpt-3.5-turbo",
                  type: str = "input") -> float:
    """
    估算API调用成本

    Args:
        tokens: token数量
        model: 模型名称
        type: 类型（input/output）

    Returns:
        预估成本（美元）
    """
    # 价格表（每1000 tokens的价格，美元）
    pricing = {
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
    }

    # 默认价格（如果模型不在列表中）
    default_price = {'input': 0.001, 'output': 0.002}

    model_pricing = pricing.get(model, default_price)
    price_per_1k = model_pricing.get(type, 0.001)

    return (tokens / 1000) * price_per_1k


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简化版本，使用Jaccard相似度）

    Args:
        text1: 第一个文本
        text2: 第二个文本

    Returns:
        相似度分数（0-1）
    """
    # 分词（简单按空格分割）
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    # 计算交集和并集
    intersection = words1 & words2
    union = words1 | words2

    if not union:
        return 0.0

    # Jaccard相似度
    return len(intersection) / len(union)


def merge_dicts(*dicts: Dict) -> Dict:
    """
    合并多个字典

    Args:
        *dicts: 要合并的字典

    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


if __name__ == "__main__":
    # 测试代码
    print("=== 工具函数测试 ===\n")

    # 测试token计数
    text = "Hello world! 这是一个测试文本。"
    tokens = count_tokens(text)
    print(f"文本: {text}")
    print(f"Token数: {tokens}\n")

    # 测试实体提取
    code_text = """
    def process_data(filename):
        with open('data.json') as f:
            return json.load(f)

    class DataProcessor:
        def __init__(self):
            self.data = []
    """
    entities = extract_entities(code_text)
    print(f"提取的实体: {entities}\n")

    # 测试进度条
    print("进度条示例:")
    for i in range(0, 101, 10):
        print_progress_bar(i / 100)

    # 测试统计信息
    stats = {
        'conversation': {
            'total_messages': 15,
            'user_messages': 8,
            'assistant_messages': 7,
            'current_tokens': 2240,
            'max_tokens': 8000,
            'usage_percentage': 0.28
        },
        'compression': {
            'count': 1,
            'total_saved': 5264,
            'avg_ratio': 0.7,
            'retention_rate': 0.95
        }
    }
    print_statistics(stats)
