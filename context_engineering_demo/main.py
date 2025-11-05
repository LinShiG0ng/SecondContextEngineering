"""
命令行交互式演示程序
支持与真实大模型对话和上下文压缩演示
"""

import asyncio
import sys
from typing import Optional

from context_engineering_demo.config_loader import load_config, is_first_run
from context_engineering_demo.llm_client import LLMClient
from context_engineering_demo.context_manager import ContextManager
from context_engineering_demo.utils import (
    print_colored, print_box, print_progress_bar, print_statistics
)


class InteractiveDemo:
    """交互式演示程序"""

    def __init__(self):
        """初始化演示程序"""
        self.config = None
        self.llm_client = None
        self.context_manager = None
        self.running = True

    async def initialize(self):
        """初始化系统"""
        # 加载配置
        print_box("🧠 上下文工程演示系统", char='=')
        print()

        self.config = load_config()

        # 初始化LLM客户端
        llm_config = self.config.get('llm', {})
        self.llm_client = LLMClient(llm_config)

        # 初始化上下文管理器
        max_tokens = self.config.get('context', {}).get('max_tokens', 8000)
        self.context_manager = ContextManager(max_tokens=max_tokens)

        # 显示配置信息
        print(f"当前模型: {llm_config.get('model')}")
        print(f"Token限制: {max_tokens:,}")
        print(f"压缩阈值: {self.config.get('context', {}).get('auto_compact_threshold', 0.92)*100:.0f}%")
        print()

        # 测试连接（可选）
        if llm_config.get('api_key'):
            print("🔄 测试API连接...")
            try:
                await self.llm_client.test_connection()
            except Exception as e:
                print_colored(f"⚠️  API连接测试失败: {e}", 'yellow')
                print_colored("提示：你仍然可以使用系统，但无法调用真实API", 'yellow')
        print()

        # 显示帮助
        self.show_welcome()

    def show_welcome(self):
        """显示欢迎信息"""
        print_colored("💡 提示：输入 /help 查看所有命令", 'cyan')
        print()

    def show_help(self):
        """显示帮助信息"""
        print_box("📖 帮助信息")
        print()
        print("可用命令:")
        print("  /help       - 显示帮助信息")
        print("  /stats      - 显示统计信息")
        print("  /history    - 查看完整历史")
        print("  /compress   - 手动触发压缩")
        print("  /reset      - 重置对话")
        print("  /config     - 重新配置API")
        print("  /test       - 测试API连接")
        print("  /compare    - 对比压缩效果")
        print("  /export     - 导出对话历史")
        print("  /quit       - 退出程序")
        print()
        print("直接输入消息即可与AI对话")
        print()

    async def run(self):
        """运行主循环"""
        await self.initialize()

        while self.running:
            try:
                # 显示token使用率
                usage_rate = self.context_manager.calculate_usage()
                print_progress_bar(usage_rate)
                print()

                # 获取用户输入
                try:
                    user_input = input("💬 用户> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    self.running = False
                    break

                if not user_input:
                    continue

                # 处理命令
                if user_input.startswith('/'):
                    await self.handle_command(user_input)
                else:
                    # 处理对话
                    await self.handle_chat(user_input)

            except KeyboardInterrupt:
                print()
                print_colored("\n👋 再见！", 'cyan')
                break
            except Exception as e:
                print_colored(f"❌ 错误: {e}", 'red')

    async def handle_command(self, command: str):
        """处理命令"""
        cmd = command.lower().split()[0]

        if cmd == '/help':
            self.show_help()

        elif cmd == '/stats':
            stats = self.context_manager.get_statistics()
            print_statistics(stats)

        elif cmd == '/history':
            await self.show_history()

        elif cmd == '/compress':
            await self.manual_compress()

        elif cmd == '/reset':
            self.reset_conversation()

        elif cmd == '/config':
            await self.reconfigure()

        elif cmd == '/test':
            await self.test_api()

        elif cmd == '/compare':
            await self.compare_compression()

        elif cmd == '/export':
            self.export_conversation()

        elif cmd == '/quit' or cmd == '/exit':
            self.running = False
            print_colored("👋 再见！", 'cyan')

        else:
            print_colored(f"⚠️  未知命令: {cmd}", 'yellow')
            print_colored("输入 /help 查看帮助", 'yellow')

    async def handle_chat(self, user_message: str):
        """处理对话"""
        # 添加用户消息
        result = await self.context_manager.add_message('user', user_message)

        # 检查是否需要压缩
        if result['should_compress']:
            print_colored("\n🔄 Token使用率达到92%，触发自动压缩！\n", 'magenta', bold=True)
            compression_result = await self.context_manager.compress()

            if compression_result['success']:
                stats = compression_result['statistics']
                print_colored(f"✅ 压缩完成: 节省 {stats['tokens_saved']:,} tokens ({stats['compression_ratio']*100:.1f}%)", 'green')
                print()

        # 获取上下文
        context = await self.context_manager.get_context(user_message)

        # 调用LLM API
        print_colored("🔄 正在调用API...", 'cyan')

        try:
            response = await self.llm_client.chat(context, stream=True)
            print() # 换行

            # 添加助手响应
            await self.context_manager.add_message('assistant', response)

            print()  # 额外换行

        except Exception as e:
            print_colored(f"\n❌ API调用失败: {e}", 'red')
            print_colored("提示：请检查API配置或网络连接", 'yellow')

    async def show_history(self):
        """显示完整历史"""
        original_messages = self.context_manager.storage.get_original_messages()

        print_box(f"📜 对话历史 ({len(original_messages)} 条消息)")
        print()

        for i, msg in enumerate(original_messages, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            tokens = msg.get('tokens', 0)

            # 截断长内容
            preview = content[:100] + ('...' if len(content) > 100 else '')

            print(f"{i}. [{role}] ({tokens} tokens)")
            print(f"   {preview}")
            print()

    async def manual_compress(self):
        """手动触发压缩"""
        print_colored("🔄 执行手动压缩...\n", 'cyan')

        compression_result = await self.context_manager.compress()

        if compression_result['success']:
            stats = compression_result['statistics']
            print_colored(f"\n✅ 压缩完成！", 'green', bold=True)
            print(f"  原始: {stats['original_tokens']:,} tokens")
            print(f"  压缩后: {stats['compressed_tokens']:,} tokens")
            print(f"  节省: {stats['tokens_saved']:,} tokens ({stats['compression_ratio']*100:.1f}%)")
            print(f"  耗时: {stats['execution_time']:.2f}秒")
        else:
            print_colored(f"⚠️  {compression_result.get('message', '压缩失败')}", 'yellow')

        print()

    def reset_conversation(self):
        """重置对话"""
        confirm = input("⚠️  确定要重置对话吗？(y/n): ").strip().lower()

        if confirm == 'y':
            self.context_manager.reset()
            print_colored("✅ 对话已重置", 'green')
        else:
            print_colored("❌ 已取消", 'yellow')

        print()

    async def reconfigure(self):
        """重新配置"""
        print_colored("⚠️  重新配置功能暂未实现", 'yellow')
        print_colored("提示：请手动编辑 config.yaml 文件", 'yellow')
        print()

    async def test_api(self):
        """测试API连接"""
        print_colored("🔄 测试API连接...\n", 'cyan')

        try:
            success = await self.llm_client.test_connection()
            if not success:
                print_colored("提示：请检查API key和网络连接", 'yellow')
        except Exception as e:
            print_colored(f"❌ 测试失败: {e}", 'red')

        print()

    async def compare_compression(self):
        """对比压缩效果"""
        print_box("📊 压缩效果对比测试")
        print()

        test_query = input("输入测试问题 (直接回车使用默认): ").strip()
        if not test_query:
            test_query = "总结一下我们讨论的要点"

        print(f"\n测试问题: \"{test_query}\"\n")

        # 获取原始消息
        original_messages = self.context_manager.storage.get_original_messages()

        if len(original_messages) < 5:
            print_colored("⚠️  消息数量不足，无法进行对比测试", 'yellow')
            print()
            return

        # 测试1: 使用原始上下文
        print_colored("【使用原始上下文】", 'cyan', bold=True)
        original_context = original_messages.copy()
        original_tokens = sum(msg.get('tokens', 0) for msg in original_context)

        print(f"🔄 正在调用API ({len(original_context)}条消息, {original_tokens:,} tokens)...")

        try:
            import time as time_module
            start_time = time_module.time()
            response_original = await self.llm_client.chat(
                original_context + [{'role': 'user', 'content': test_query}],
                stream=False
            )
            time_original = time_module.time() - start_time

            print(f"🤖 响应: {response_original[:100]}...")
            print(f"⏱️  响应时间: {time_original:.2f}秒")
            print(f"💰 成本估算: ${self.llm_client.estimate_cost(original_tokens, len(response_original)//4):.4f}")
            print()

        except Exception as e:
            print_colored(f"❌ API调用失败: {e}", 'red')
            response_original = ""
            time_original = 0

        # 测试2: 使用压缩上下文
        print_colored("【使用压缩上下文】", 'cyan', bold=True)

        # 先执行压缩
        compression_result = await self.context_manager.compressor.compress(original_messages)
        compressed_context = compression_result['compressed_messages']
        compressed_tokens = sum(msg.get('tokens', 0) for msg in compressed_context)

        print(f"🔄 正在调用API ({len(compressed_context)}条消息, {compressed_tokens:,} tokens)...")

        try:
            start_time = time_module.time()
            response_compressed = await self.llm_client.chat(
                compressed_context + [{'role': 'user', 'content': test_query}],
                stream=False
            )
            time_compressed = time_module.time() - start_time

            print(f"🤖 响应: {response_compressed[:100]}...")
            print(f"⏱️  响应时间: {time_compressed:.2f}秒")
            print(f"💰 成本估算: ${self.llm_client.estimate_cost(compressed_tokens, len(response_compressed)//4):.4f}")
            print()

        except Exception as e:
            print_colored(f"❌ API调用失败: {e}", 'red')
            response_compressed = ""
            time_compressed = 1

        # 对比结果
        if response_original and response_compressed:
            print_box("📈 对比结果")
            print()

            token_reduction = (1 - compressed_tokens / original_tokens) * 100
            speed_increase = time_original / time_compressed if time_compressed > 0 else 0

            print(f"✨ Token节省: {token_reduction:.1f}%")
            print(f"🚀 速度提升: {speed_increase:.1f}x")
            print(f"💵 成本降低: {token_reduction:.1f}%")

            # 计算相似度
            from context_engineering_demo.utils import calculate_similarity
            similarity = calculate_similarity(response_original, response_compressed)
            print(f"🎯 响应相似度: {similarity*100:.1f}%")

            print()

    def export_conversation(self):
        """导出对话"""
        filepath = self.context_manager.export_json()
        print_colored(f"✅ 对话已导出到: {filepath}", 'green')
        print()


async def main():
    """主函数"""
    demo = InteractiveDemo()
    await demo.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(0)
