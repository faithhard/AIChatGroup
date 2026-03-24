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

    sys.path.insert(0, resource_dir)
    from config import HOST, PORT

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
