"""
BotGroup 打包脚本
运行方式：python build.py
打包完成后 exe 在 dist/BotGroup.exe
"""
import subprocess
import sys
import os

# 确保 PyInstaller 已安装
try:
    import PyInstaller
except ImportError:
    print("正在安装 PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

base_dir = os.path.dirname(os.path.abspath(__file__))
sep = os.pathsep  # Windows 是 ;

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--console",            # 保留控制台窗口，方便查看日志
    "--name", "BotGroup",
    # 打包静态资源和模块
    "--add-data", f"{os.path.join(base_dir, 'templates')}{sep}templates",
    "--add-data", f"{os.path.join(base_dir, 'static')}{sep}static",
    "--add-data", f"{os.path.join(base_dir, 'config.py')}{sep}.",
    "--add-data", f"{os.path.join(base_dir, 'ai_service.py')}{sep}.",
    "--add-data", f"{os.path.join(base_dir, 'database.py')}{sep}.",
    "--add-data", f"{os.path.join(base_dir, 'main.py')}{sep}.",
    # 收集完整子模块（main.py 作为 add-data 不会被自动分析依赖）
    "--collect-submodules", "fastapi",
    "--collect-submodules", "starlette",
    "--collect-submodules", "uvicorn",
    "--collect-submodules", "sqlalchemy",
    "--collect-submodules", "anyio",
    "--collect-submodules", "httpx",
    "--collect-submodules", "httpcore",
    "--collect-submodules", "pydantic",
    "--collect-submodules", "pydantic_core",
    "--hidden-import", "multipart",
    "--hidden-import", "python_multipart",
    "--hidden-import", "jinja2",
    "--hidden-import", "markupsafe",
    "--hidden-import", "email.mime.multipart",
    "--hidden-import", "h11",
    "--hidden-import", "certifi",
    "--hidden-import", "idna",
    "--hidden-import", "sniffio",
    # 入口文件
    os.path.join(base_dir, "launcher.py"),
]

print("=" * 50)
print("  BotGroup 打包工具")
print("=" * 50)
print(f"\n项目目录: {base_dir}")
print("开始打包，请稍候...\n")

result = subprocess.run(cmd, cwd=base_dir)

if result.returncode == 0:
    exe_path = os.path.join(base_dir, "dist", "BotGroup.exe")
    print(f"\n{'=' * 50}")
    print(f"  [OK] 打包成功!")
    print(f"{'=' * 50}")
    print(f"\n  exe 路径: {exe_path}")
    print(f"\n  使用方法:")
    print(f"    1. 将 dist/BotGroup.exe 复制到任意目录")
    print(f"    2. 双击运行，浏览器自动打开")
    print(f"    3. chat.db 会自动创建在 exe 同目录")
    print()
else:
    print(f"\n{'=' * 50}")
    print(f"  [FAIL] 打包失败，请检查上方错误信息")
    print(f"{'=' * 50}")
