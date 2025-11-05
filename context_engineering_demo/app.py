"""
Web应用入口
FastAPI + Uvicorn实现的Web UI界面
"""

import uvicorn
from context_engineering_demo.web.api import app
from context_engineering_demo import config as default_config


def main():
    """启动Web服务器"""
    print("=" * 60)
    print("🌐 上下文工程演示系统 - Web UI")
    print("=" * 60)
    print()
    print(f"📍 访问地址: http://{default_config.WEB_HOST}:{default_config.WEB_PORT}")
    print(f"📖 API文档: http://{default_config.WEB_HOST}:{default_config.WEB_PORT}/docs")
    print()
    print("提示：按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    # 启动服务器
    uvicorn.run(
        app,
        host=default_config.WEB_HOST,
        port=default_config.WEB_PORT,
        reload=default_config.WEB_RELOAD,
        log_level="info"
    )


if __name__ == "__main__":
    main()
