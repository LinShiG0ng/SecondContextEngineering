"""
默认配置参数
定义所有的阈值和系统参数
"""

# ============================================================
# Token限制配置
# ============================================================

# 模拟的上下文窗口大小（tokens）
MAX_TOKENS = 8000

# 60% - 黄色警告阈值
WARNING_THRESHOLD = 0.6

# 80% - 红色警告阈值
ERROR_THRESHOLD = 0.8

# 92% - 自动压缩触发阈值
AUTO_COMPACT_THRESHOLD = 0.92


# ============================================================
# 存储配置
# ============================================================

# 短期记忆保留的消息数（最近的N条消息完整保留）
SHORT_TERM_SIZE = 5

# 中期记忆最大消息数（压缩后的历史）
MID_TERM_SIZE = 30

# 工作空间目录
WORKSPACE_DIR = "./workspace"

# 知识库文件路径
KNOWLEDGE_BASE_PATH = "./workspace/knowledge.json"


# ============================================================
# 压缩配置
# ============================================================

# 目标压缩率（70%表示压缩后保留30%的tokens）
TARGET_COMPRESSION_RATIO = 0.70

# 最低信息保留率（90%表示至少保留90%的关键信息）
MIN_QUALITY_RETENTION = 0.90

# 消息分类阈值
MESSAGE_CLASSIFICATION = {
    'critical_keywords': [
        'error', 'exception', 'bug', 'fix', 'critical', 'important',
        '错误', '异常', '修复', '重要', '关键'
    ],
    'important_keywords': [
        'implement', 'create', 'design', 'refactor', 'optimize',
        '实现', '创建', '设计', '重构', '优化'
    ]
}


# ============================================================
# System Prompt特殊处理 ⭐
# ============================================================

# 是否完整保留系统提示词（不压缩）
PRESERVE_SYSTEM_PROMPTS = True

# 系统角色标识
SYSTEM_ROLE_NAME = "system"


# ============================================================
# 注入配置
# ============================================================

# 相关性阈值（低于此值的片段不会被注入）
RELEVANCE_THRESHOLD = 0.5

# 最多注入的片段数量
MAX_INJECTED_SEGMENTS = 3


# ============================================================
# Web UI配置 ⭐
# ============================================================

# Web服务器地址
WEB_HOST = "127.0.0.1"

# Web服务器端口
WEB_PORT = 8000

# 是否开启调试模式
WEB_DEBUG = False

# 是否自动重载（开发时使用）
WEB_RELOAD = False

# 是否启用跨域（CORS）
ENABLE_CORS = True

# 是否启用WebSocket（实时通信）
WEBSOCKET_ENABLED = True


# ============================================================
# LLM API默认配置
# ============================================================

# 默认API提供商（openai/anthropic/ollama/custom）
DEFAULT_LLM_PROVIDER = "openai"

# 默认模型
DEFAULT_LLM_MODEL = "gpt-3.5-turbo"

# 默认温度
DEFAULT_TEMPERATURE = 0.7

# 是否启用流式输出
DEFAULT_STREAM = True

# API超时时间（秒）
API_TIMEOUT = 60

# API重试次数
API_RETRY_COUNT = 3

# API重试延迟（秒）
API_RETRY_DELAY = 2


# ============================================================
# 模型配置映射
# ============================================================

# 各个提供商支持的模型
SUPPORTED_MODELS = {
    'openai': [
        'gpt-3.5-turbo',
        'gpt-4',
        'gpt-4-turbo',
        'gpt-4o',
        'gpt-4o-mini'
    ],
    'anthropic': [
        'claude-3-5-sonnet-20241022',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307'
    ],
    'ollama': [
        'qwen2.5:7b',
        'llama3.1:8b',
        'mistral:7b',
        'deepseek-coder:6.7b'
    ]
}

# 各个模型的最大token限制
MODEL_MAX_TOKENS = {
    'gpt-3.5-turbo': 16385,
    'gpt-4': 8192,
    'gpt-4-turbo': 128000,
    'gpt-4o': 128000,
    'gpt-4o-mini': 128000,
    'claude-3-5-sonnet-20241022': 200000,
    'claude-3-opus-20240229': 200000,
    'claude-3-sonnet-20240229': 200000,
    'claude-3-haiku-20240307': 200000,
    'qwen2.5:7b': 32768,
    'llama3.1:8b': 128000,
}


# ============================================================
# 成本估算配置
# ============================================================

# 各个模型的价格（美元/1000 tokens）
MODEL_PRICING = {
    'gpt-3.5-turbo': {
        'input': 0.0005,
        'output': 0.0015
    },
    'gpt-4': {
        'input': 0.03,
        'output': 0.06
    },
    'gpt-4-turbo': {
        'input': 0.01,
        'output': 0.03
    },
    'gpt-4o': {
        'input': 0.0025,
        'output': 0.01
    },
    'gpt-4o-mini': {
        'input': 0.00015,
        'output': 0.0006
    },
    'claude-3-5-sonnet-20241022': {
        'input': 0.003,
        'output': 0.015
    },
    'claude-3-opus-20240229': {
        'input': 0.015,
        'output': 0.075
    },
    'claude-3-sonnet-20240229': {
        'input': 0.003,
        'output': 0.015
    },
    'claude-3-haiku-20240307': {
        'input': 0.00025,
        'output': 0.00125
    },
    # Ollama本地模型免费
    'qwen2.5:7b': {
        'input': 0.0,
        'output': 0.0
    },
    'llama3.1:8b': {
        'input': 0.0,
        'output': 0.0
    },
}


# ============================================================
# 终端美化配置
# ============================================================

# 是否启用彩色输出
ENABLE_COLOR = True

# 进度条宽度
PROGRESS_BAR_WIDTH = 40

# 统计信息框宽度
STATS_BOX_WIDTH = 60


# ============================================================
# 日志配置
# ============================================================

# 是否启用详细日志
VERBOSE_LOGGING = False

# 日志级别（DEBUG/INFO/WARNING/ERROR）
LOG_LEVEL = "INFO"

# 日志文件路径
LOG_FILE_PATH = "./workspace/app.log"


# ============================================================
# 导出配置
# ============================================================

# 导出格式（json/markdown）
DEFAULT_EXPORT_FORMAT = "json"

# 导出目录
EXPORT_DIR = "./exports"


# ============================================================
# 配置验证函数
# ============================================================

def validate_config() -> bool:
    """
    验证配置参数的合法性

    Returns:
        配置是否有效
    """
    # 检查阈值范围
    if not (0 <= WARNING_THRESHOLD <= 1):
        print("错误: WARNING_THRESHOLD 必须在 0-1 之间")
        return False

    if not (0 <= ERROR_THRESHOLD <= 1):
        print("错误: ERROR_THRESHOLD 必须在 0-1 之间")
        return False

    if not (0 <= AUTO_COMPACT_THRESHOLD <= 1):
        print("错误: AUTO_COMPACT_THRESHOLD 必须在 0-1 之间")
        return False

    # 检查阈值顺序
    if not (WARNING_THRESHOLD < ERROR_THRESHOLD < AUTO_COMPACT_THRESHOLD):
        print("错误: 阈值必须满足 WARNING < ERROR < AUTO_COMPACT")
        return False

    # 检查压缩率
    if not (0 < TARGET_COMPRESSION_RATIO < 1):
        print("错误: TARGET_COMPRESSION_RATIO 必须在 0-1 之间")
        return False

    # 检查信息保留率
    if not (0 < MIN_QUALITY_RETENTION <= 1):
        print("错误: MIN_QUALITY_RETENTION 必须在 0-1 之间")
        return False

    return True


def get_model_config(provider: str, model: str) -> dict:
    """
    获取指定模型的配置

    Args:
        provider: API提供商
        model: 模型名称

    Returns:
        模型配置字典
    """
    return {
        'provider': provider,
        'model': model,
        'max_tokens': MODEL_MAX_TOKENS.get(model, MAX_TOKENS),
        'pricing': MODEL_PRICING.get(model, {'input': 0.001, 'output': 0.002}),
        'temperature': DEFAULT_TEMPERATURE,
        'stream': DEFAULT_STREAM,
        'timeout': API_TIMEOUT,
    }


if __name__ == "__main__":
    # 测试配置验证
    print("=== 配置验证测试 ===\n")

    if validate_config():
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败")

    # 显示关键配置
    print(f"\n📊 关键配置:")
    print(f"  • Token限制: {MAX_TOKENS:,}")
    print(f"  • 警告阈值: {WARNING_THRESHOLD*100:.0f}%")
    print(f"  • 错误阈值: {ERROR_THRESHOLD*100:.0f}%")
    print(f"  • 自动压缩阈值: {AUTO_COMPACT_THRESHOLD*100:.0f}%")
    print(f"  • 目标压缩率: {TARGET_COMPRESSION_RATIO*100:.0f}%")
    print(f"  • System Prompt保留: {'是' if PRESERVE_SYSTEM_PROMPTS else '否'}")

    # 测试获取模型配置
    print(f"\n🤖 模型配置示例:")
    config = get_model_config('openai', 'gpt-3.5-turbo')
    print(f"  • 提供商: {config['provider']}")
    print(f"  • 模型: {config['model']}")
    print(f"  • 最大Tokens: {config['max_tokens']:,}")
    print(f"  • 输入价格: ${config['pricing']['input']}/1K tokens")
