import base64
import io

import requests
import subprocess
import time
import os
import sys
import threading
import zipfile
import shutil
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw

SERVER_URL = "http://192.168.2.114:5000"
is_running = True
ICON_BASE64 = "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"


def execute_remote_logic(task_id, test_name, download_url):
    print(f" 收到任务 {task_id}，正在下载项目代码...")

    project_root = os.path.dirname(os.path.dirname(__file__))
    temp_project_dir = os.path.join(project_root, "temp_project")
    zip_path = os.path.join(project_root, f"{task_id}.zip")

    try:
        resp = requests.get(download_url)
        if resp.status_code != 200:
            print("下载项目代码失败")
            return

        with open(zip_path, 'wb') as f:
            f.write(resp.content)

        if os.path.exists(temp_project_dir):
            shutil.rmtree(temp_project_dir)
        os.makedirs(temp_project_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_project_dir)
        os.remove(zip_path)
        print(f"项目代码已解压")

        req_file = os.path.join(temp_project_dir, "requirements.txt")
        if os.path.exists(req_file):
            print(" 正在安装依赖...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("依赖安装完成")

        test_file = os.path.join(temp_project_dir, "test", f"{test_name}.py")
        report_file = os.path.join(temp_project_dir, "local_report.html")
        
        if not os.path.exists(test_file):
            print(f" 未找到测试文件: {test_file}")
            return

        print(f" 正在执行: {test_name}")
        cmd = [sys.executable, "-m", "pytest", test_file, "--html=" + report_file, "--self-contained-html", "-v"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=temp_project_dir)

        if result.returncode in [0, 1]:
            print("执行成功，正在上传报告...")
            files = {'report': (os.path.basename(report_file), open(report_file, 'rb'), 'text/html')}
            screenshot_dir = os.path.join(temp_project_dir, "reports", "screenshots")
            print(screenshot_dir)
            if os.path.exists(screenshot_dir):
                for f_name in os.listdir(screenshot_dir):
                    if f_name.endswith('.png'):
                        f_path = os.path.join(screenshot_dir, f_name)
                        print(f_path)
                        files[f'screenshot_{f_name}'] = (f_name, open(f_path, 'rb'), 'image/png')

            data = {'task_id': task_id}
            upload_resp = requests.post(f"{SERVER_URL}/api/upload_report", files=files, data=data)
            for f_obj in files.values(): f_obj[1].close()
            
            if upload_resp.json().get('success'):
                print(f"任务完成！")
            else:
                print("上传失败:", upload_resp.text)
        else:
            print(f"测试失败:\n{result.stderr}")

    except Exception as e:
        print(f"执行出错: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if os.path.exists(temp_project_dir):
            shutil.rmtree(temp_project_dir)


def on_start(icon, item):
    global is_running
    is_running = True
    icon.notify("代理已启动", "自动化测试助手")


def on_stop(icon, item):
    global is_running
    is_running = False
    icon.stop()


def poll_task_loop(icon):
    global is_running
    print("轮训线程启动中...")
    print(f"{is_running}")
    while is_running:
        try:
            resp = requests.get(f"{SERVER_URL}/api/poll_task", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    task = data['data']
                    print(f" 获取到任务 {task}，正在处理...")
                    threading.Thread(target=execute_remote_logic,
                                     args=(task['task_id'], task['test_name'], task['download_url']),
                                     daemon=True).start()
        except Exception as e:
            pass
        time.sleep(3)


def cleanup_files(file_list):
    for file_path in file_list:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f" 已清理本地临时文件: {file_path}")
        except Exception as e:
            print(f"️ 清理文件 {file_path} 失败: {e}")


def get_icon_image():
    icon_bytes = base64.b64decode(ICON_BASE64)
    return Image.open(io.BytesIO(icon_bytes))

def main():
    icon = pystray.Icon("TestAgent", get_icon_image(), "自动化测试助手")
    icon.menu = pystray.Menu(
        item('状态: 监听中...', lambda: None, enabled=False),
        item('重新启动', on_start),
        item('退出程序', on_stop)
    )

    print("正在启动轮训线程...")
    t = threading.Thread(target=poll_task_loop, args=(icon,), daemon=True)
    t.start()

    icon.run()


if __name__ == '__main__':
    main()
