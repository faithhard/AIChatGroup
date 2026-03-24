"""
BotGroup 启动入口
打包为 exe 后双击运行，自动启动服务并打开浏览器
"""
import sys
import os
import threading
import webbrowser
import time


def get_resource_dir():
    """PyInstaller 打包后资源解压到 sys._MEIPASS，开发时就是脚本所在目录"""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_runtime_dir():
    """运行时数据目录（chat.db、uploads 等写到 exe 所在目录，而非临时目录）"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def open_browser(port: int):
    time.sleep(1.8)
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    resource_dir = get_resource_dir()
    runtime_dir = get_runtime_dir()

    # 工作目录切到资源目录（templates/、static/ 等在这里）
    os.chdir(resource_dir)

    # 确保运行时目录下有 uploads 文件夹
    uploads_dir = os.path.join(runtime_dir, "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # 让 SQLite 数据库写到 exe 同级目录
    os.environ["BOTGROUP_DB_DIR"] = runtime_dir

    # 如果 exe 旁边没有 config.py，从打包资源里复制一份出来
    runtime_config = os.path.join(runtime_dir, "config.py")
    resource_config = os.path.join(resource_dir, "config.py")
    if not os.path.exists(runtime_config) and os.path.exists(resource_config):
        import shutil
        shutil.copy2(resource_config, runtime_config)
        print(f"已生成配置文件: {runtime_config}")
        print("请编辑 config.py 填入你的 API Key，然后重新运行。")

    # ★ 关键：用 importlib 强制从 exe 同目录加载 config.py
    #   PyInstaller 的 FrozenImporter 优先级高于 sys.path，
    #   普通 import config 永远命中打包内的旧文件。
    #   这里手动加载后塞进 sys.modules，后续所有模块
    #   （包括 main.py 的 from config import ...）都会拿到这份。
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", runtime_config)
    config_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_mod)
    sys.modules["config"] = config_mod  # 覆盖缓存

    HOST = config_mod.HOST
    PORT = config_mod.PORT
    print(f"配置文件: {runtime_config}")
    print(f"默认 Bot 数量: {len(config_mod.DEFAULT_BOTS)}")
    for b in config_mod.DEFAULT_BOTS:
        print(f"  - {b['name']} ({b['model']}) -> {b['base_url']}")

    threading.Thread(target=open_browser, args=(PORT,), daemon=True).start()

    print(f"BotGroup 启动中... 访问 http://127.0.0.1:{PORT}")
    print(f"数据目录: {runtime_dir}")

    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
    )
