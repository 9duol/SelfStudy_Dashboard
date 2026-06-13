import requests
import json
import os
import sys
import tempfile
import shutil
from tkinter import messagebox
import threading
import urllib.request
from packaging import version


class Updater:
    def __init__(self, current_version, repo_owner="lic06", repo_name="Selfstudy_boards"):
        """
        初始化更新器
        
        Args:
            current_version (str): 当前程序版本号
            repo_owner (str): GitHub仓库所有者
            repo_name (str): GitHub仓库名称
        """
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"
        self.download_dir = tempfile.gettempdir()
        
    def check_for_updates(self, callback=None):
        """
        检查更新
        
        Args:
            callback (function): 检查完成后的回调函数
        """
        def _check():
            try:
                # 获取最新的发布版本
                response = requests.get(self.api_url, timeout=10)
                response.raise_for_status()
                releases = response.json()
                
                if not releases:
                    if callback:
                        callback(None, "未找到任何发布版本")
                    return
                
                # 获取最新版本
                latest_release = releases[0]
                latest_version = latest_release["tag_name"].lstrip("v")  # 移除版本号前的'v'
                
                # 比较版本号
                if version.parse(latest_version) > version.parse(self.current_version):
                    # 有新版本
                    update_info = {
                        "version": latest_version,
                        "name": latest_release["name"],
                        "body": latest_release["body"],
                        "published_at": latest_release["published_at"],
                        "assets": latest_release["assets"]
                    }
                    if callback:
                        callback(update_info, None)
                else:
                    # 当前版本是最新的
                    if callback:
                        callback(None, None)
            except requests.exceptions.RequestException as e:
                if callback:
                    callback(None, f"网络错误: {str(e)}")
            except Exception as e:
                if callback:
                    callback(None, f"检查更新时出错: {str(e)}")
        
        # 在单独的线程中执行检查更新操作
        thread = threading.Thread(target=_check, daemon=True)
        thread.start()
    
    def download_latest_release(self, assets, progress_callback=None, completion_callback=None):
        """
        下载最新版本的exe文件
        
        Args:
            assets (list): 发布资产列表
            progress_callback (function): 进度回调函数
            completion_callback (function): 完成回调函数
        """
        def _download():
            try:
                # 查找exe文件
                exe_asset = None
                for asset in assets:
                    if asset["name"].endswith(".exe"):
                        exe_asset = asset
                        break
                
                if not exe_asset:
                    if completion_callback:
                        completion_callback(None, "未找到exe文件")
                    return
                
                # 下载文件
                download_url = exe_asset["browser_download_url"]
                filename = exe_asset["name"]
                temp_file_path = os.path.join(self.download_dir, filename)
                
                # 下载文件并报告进度
                def report_progress(block_num, block_size, total_size):
                    if progress_callback:
                        downloaded = block_num * block_size
                        if total_size > 0:
                            percent = min(100, (downloaded * 100) // total_size)
                            progress_callback(percent, f"正在下载... {downloaded}/{total_size} 字节")
                        else:
                            progress_callback(0, f"正在下载... {downloaded} 字节")
                
                urllib.request.urlretrieve(download_url, temp_file_path, reporthook=report_progress)
                
                if completion_callback:
                    completion_callback(temp_file_path, None)
            except Exception as e:
                if completion_callback:
                    completion_callback(None, f"下载失败: {str(e)}")
        
        # 在单独的线程中执行下载操作
        thread = threading.Thread(target=_download, daemon=True)
        thread.start()
    
    def apply_update(self, downloaded_file_path):
        """
        应用更新（替换当前程序文件）
        
        Args:
            downloaded_file_path (str): 下载的文件路径
        """
        try:
            # 获取当前执行文件的路径
            current_exe = sys.executable
            
            # 创建备份
            backup_path = current_exe + ".bak"
            shutil.copy2(current_exe, backup_path)
            
            # 替换文件
            shutil.copy2(downloaded_file_path, current_exe)
            
            # 删除临时文件
            os.remove(downloaded_file_path)
            
            return True, "更新成功，请重启程序"
        except Exception as e:
            return False, f"更新失败: {str(e)}"