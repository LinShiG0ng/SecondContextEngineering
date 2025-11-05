"""
配置加载与管理模块
支持多种配置方式：环境变量、YAML文件、交互式配置向导
"""

import os
import json
import yaml
from typing import Dict, Optional, Any
from pathlib import Path
import getpass

# 导入默认配置
from . import config as default_config


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置加载器

        Args:
            config_file: 配置文件路径（可选）
        """
        self.config_file = config_file or "config.yaml"
        self.config = {}

    def load_config(self) -> Dict:
        """
        加载配置（按优先级）

        优先级：命令行参数 > 环境变量 > 配置文件 > 默认值

        Returns:
            完整的配置字典
        """
        # 1. 加载默认配置
        self.config = self._load_default_config()

        # 2. 加载配置文件（如果存在）
        if os.path.exists(self.config_file):
            file_config = self._load_from_file(self.config_file)
            self.config = self._merge_configs(self.config, file_config)

        # 3. 加载环境变量
        env_config = self._load_from_env()
        self.config = self._merge_configs(self.config, env_config)

        # 4. 验证配置
        if not self.validate_config(self.config):
            raise ValueError("配置验证失败")

        return self.config

    def _load_default_config(self) -> Dict:
        """
        加载默认配置

        Returns:
            默认配置字典
        """
        return {
            'llm': {
                'provider': default_config.DEFAULT_LLM_PROVIDER,
                'model': default_config.DEFAULT_LLM_MODEL,
                'api_key': None,
                'base_url': None,
                'temperature': default_config.DEFAULT_TEMPERATURE,
                'stream': default_config.DEFAULT_STREAM,
                'timeout': default_config.API_TIMEOUT,
            },
            'context': {
                'max_tokens': default_config.MAX_TOKENS,
                'warning_threshold': default_config.WARNING_THRESHOLD,
                'error_threshold': default_config.ERROR_THRESHOLD,
                'auto_compact_threshold': default_config.AUTO_COMPACT_THRESHOLD,
                'target_compression_ratio': default_config.TARGET_COMPRESSION_RATIO,
            },
            'storage': {
                'workspace_dir': default_config.WORKSPACE_DIR,
                'short_term_size': default_config.SHORT_TERM_SIZE,
                'mid_term_size': default_config.MID_TERM_SIZE,
            },
            'web': {
                'host': default_config.WEB_HOST,
                'port': default_config.WEB_PORT,
                'debug': default_config.WEB_DEBUG,
                'enable_cors': default_config.ENABLE_CORS,
            },
            'system': {
                'preserve_system_prompts': default_config.PRESERVE_SYSTEM_PROMPTS,
                'verbose_logging': default_config.VERBOSE_LOGGING,
            }
        }

    def _load_from_file(self, filepath: str) -> Dict:
        """
        从文件加载配置

        Args:
            filepath: 配置文件路径

        Returns:
            配置字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.yaml') or filepath.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                elif filepath.endswith('.json'):
                    return json.load(f)
                else:
                    print(f"⚠️  不支持的配置文件格式: {filepath}")
                    return {}
        except Exception as e:
            print(f"⚠️  加载配置文件失败: {e}")
            return {}

    def _load_from_env(self) -> Dict:
        """
        从环境变量加载配置

        环境变量命名规则：
        - LLM_PROVIDER
        - LLM_MODEL
        - LLM_API_KEY
        - LLM_BASE_URL
        - MAX_TOKENS
        等等...

        Returns:
            配置字典
        """
        config = {}

        # LLM配置
        if os.getenv('LLM_PROVIDER'):
            config.setdefault('llm', {})['provider'] = os.getenv('LLM_PROVIDER')

        if os.getenv('LLM_MODEL'):
            config.setdefault('llm', {})['model'] = os.getenv('LLM_MODEL')

        if os.getenv('LLM_API_KEY'):
            config.setdefault('llm', {})['api_key'] = os.getenv('LLM_API_KEY')

        if os.getenv('LLM_BASE_URL'):
            config.setdefault('llm', {})['base_url'] = os.getenv('LLM_BASE_URL')

        if os.getenv('OPENAI_API_KEY'):
            config.setdefault('llm', {})['api_key'] = os.getenv('OPENAI_API_KEY')

        if os.getenv('ANTHROPIC_API_KEY'):
            config.setdefault('llm', {})['api_key'] = os.getenv('ANTHROPIC_API_KEY')

        # 上下文配置
        if os.getenv('MAX_TOKENS'):
            config.setdefault('context', {})['max_tokens'] = int(os.getenv('MAX_TOKENS'))

        # Web配置
        if os.getenv('WEB_PORT'):
            config.setdefault('web', {})['port'] = int(os.getenv('WEB_PORT'))

        return config

    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """
        合并配置字典（深度合并）

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result

    def validate_config(self, config: Dict) -> bool:
        """
        验证配置的合法性

        Args:
            config: 配置字典

        Returns:
            配置是否有效
        """
        # 验证必需的配置项
        if 'llm' not in config:
            print("❌ 缺少LLM配置")
            return False

        # 验证阈值
        context = config.get('context', {})
        if context:
            thresholds = [
                context.get('warning_threshold', 0.6),
                context.get('error_threshold', 0.8),
                context.get('auto_compact_threshold', 0.92)
            ]

            if not all(0 <= t <= 1 for t in thresholds):
                print("❌ 阈值必须在0-1之间")
                return False

            if not (thresholds[0] < thresholds[1] < thresholds[2]):
                print("❌ 阈值顺序错误（warning < error < auto_compact）")
                return False

        return True

    def save_config(self, config: Dict, filepath: Optional[str] = None):
        """
        保存配置到文件

        Args:
            config: 配置字典
            filepath: 保存路径（可选）
        """
        filepath = filepath or self.config_file

        try:
            # 创建目录（如果不存在）
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                if filepath.endswith('.yaml') or filepath.endswith('.yml'):
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                elif filepath.endswith('.json'):
                    json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"✅ 配置已保存到: {filepath}")

        except Exception as e:
            print(f"❌ 保存配置失败: {e}")

    def interactive_setup(self) -> Dict:
        """
        交互式配置向导（首次运行时使用）

        Returns:
            用户配置的字典
        """
        print("\n" + "=" * 60)
        print("🚀 欢迎使用上下文工程演示系统！")
        print("=" * 60)
        print("\n检测到首次运行，请配置LLM API：\n")

        config = self._load_default_config()

        # 1. 选择API提供商
        print("1️⃣  选择API提供商:")
        print("   [1] OpenAI (GPT-3.5/4)")
        print("   [2] Anthropic (Claude)")
        print("   [3] Ollama (本地模型)")
        print("   [4] 自定义API")

        while True:
            choice = input("\n请选择 (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                break
            print("⚠️  无效选择，请重新输入")

        provider_map = {
            '1': 'openai',
            '2': 'anthropic',
            '3': 'ollama',
            '4': 'custom'
        }
        provider = provider_map[choice]
        config['llm']['provider'] = provider

        # 2. 配置API Key（Ollama除外）
        if provider != 'ollama':
            print(f"\n2️⃣  输入API Key:")
            api_key = getpass.getpass("API Key: ").strip()
            config['llm']['api_key'] = api_key

            # 可选：自定义Base URL
            if provider == 'custom':
                print(f"\n   输入API Base URL (例如: https://api.openai.com/v1):")
                base_url = input("Base URL: ").strip()
                if base_url:
                    config['llm']['base_url'] = base_url

        # 3. 选择模型
        print(f"\n3️⃣  选择模型:")

        if provider == 'openai':
            models = [
                ('gpt-3.5-turbo', '推荐, 便宜'),
                ('gpt-4', '更强大'),
                ('gpt-4-turbo', '最新'),
            ]
        elif provider == 'anthropic':
            models = [
                ('claude-3-5-sonnet-20241022', '推荐'),
                ('claude-3-opus-20240229', '最强大'),
                ('claude-3-haiku-20240307', '最快'),
            ]
        elif provider == 'ollama':
            models = [
                ('qwen2.5:7b', '推荐，中文好'),
                ('llama3.1:8b', '英文好'),
                ('deepseek-coder:6.7b', '编程专用'),
            ]
        else:
            models = [('gpt-3.5-turbo', '默认')]

        for i, (model, desc) in enumerate(models, 1):
            print(f"   [{i}] {model} ({desc})")

        while True:
            model_choice = input(f"\n请选择 (1-{len(models)}): ").strip()
            if model_choice.isdigit() and 1 <= int(model_choice) <= len(models):
                break
            print("⚠️  无效选择，请重新输入")

        config['llm']['model'] = models[int(model_choice) - 1][0]

        # 4. 设置Token限制
        print(f"\n4️⃣  设置Token限制:")
        while True:
            token_input = input("最大Tokens (建议4000-8000，直接回车使用8000): ").strip()
            if not token_input:
                config['context']['max_tokens'] = 8000
                break
            if token_input.isdigit() and 1000 <= int(token_input) <= 200000:
                config['context']['max_tokens'] = int(token_input)
                break
            print("⚠️  请输入1000-200000之间的数字")

        # 5. Ollama特殊配置
        if provider == 'ollama':
            print(f"\n   Ollama服务地址:")
            ollama_url = input("URL (直接回车使用 http://localhost:11434): ").strip()
            if not ollama_url:
                ollama_url = "http://localhost:11434"
            config['llm']['base_url'] = ollama_url

        # 保存配置
        print(f"\n✅ 配置完成！")
        self.save_config(config)

        # 测试连接
        test = input("\n是否现在测试连接？(y/n): ").strip().lower()
        if test == 'y':
            print("🔄 测试中...")
            # 这里会在实现llm_client后进行测试
            print("⚠️  提示：实际测试将在启动时进行")

        return config

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的路径）

        Args:
            key: 配置键（如 'llm.provider'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set_config(self, key: str, value: Any):
        """
        设置配置项

        Args:
            key: 配置键（如 'llm.provider'）
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value


def load_config(config_file: Optional[str] = None) -> Dict:
    """
    便捷函数：加载配置

    Args:
        config_file: 配置文件路径

    Returns:
        配置字典
    """
    loader = ConfigLoader(config_file)

    # 检查配置文件是否存在
    if not os.path.exists(loader.config_file):
        # 首次运行，启动交互式配置
        print("ℹ️  未找到配置文件，启动配置向导...")
        return loader.interactive_setup()

    # 加载现有配置
    return loader.load_config()


def is_first_run() -> bool:
    """
    检查是否首次运行

    Returns:
        是否首次运行
    """
    return not os.path.exists("config.yaml")


if __name__ == "__main__":
    # 测试配置加载
    print("=== 配置加载测试 ===\n")

    loader = ConfigLoader()

    if is_first_run():
        print("检测到首次运行")
        config = loader.interactive_setup()
    else:
        print("加载现有配置")
        config = loader.load_config()

    print(f"\n📊 当前配置:")
    print(json.dumps(config, indent=2, ensure_ascii=False))
