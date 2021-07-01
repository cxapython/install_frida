# -*- coding: utf-8 -*-
# @时间 : 2020/10/28 10:48 下午
# @作者 : 陈祥安
# @文件名 : install_frida.py
# @公众号: Python学习开发

import os
import shutil
import subprocess
import sys
import traceback

import requests
import six
from loguru import logger
from tqdm import tqdm

_temp = os.path.dirname(os.path.abspath(__file__))
frida_server_path = os.path.join(_temp, "frida_server")
adb_path = os.path.join(_temp, "adb")

if not os.path.exists(frida_server_path):
    os.makedirs(frida_server_path)


def download_from_url(url, dst):
    response = requests.get(url, stream=True)
    file_size = int(response.headers['content-length'])
    if os.path.exists(dst):
        first_byte = os.path.getsize(dst)
    else:
        first_byte = 0
    if first_byte >= file_size:
        return file_size
    header = {"Range": f"bytes={first_byte}-{file_size}"}
    pbar = tqdm(
        total=file_size, initial=first_byte,
        unit='B', unit_scale=True, desc=dst)
    req = requests.get(url, headers=header, stream=True)
    with(open(dst, 'ab')) as f:
        for chunk in req.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                pbar.update(1024)
    pbar.close()
    return file_size


class IsNotPython3(ValueError):
    def __str__(self):
        return "请安装python3"


def adb_operation(fs_file):
    """

    :param fs_file:
    :return:
    """
    logger.info("hluda-server安装到手机")
    try:
        adb_shell = subprocess.run(f'{adb_path} push {fs_file} /data/local/tmp', check=True, shell=True,
                                   stdout=subprocess.PIPE)
        logger.info(adb_shell.stdout.decode("utf-8"))
        logger.info("安装成功，准备修改权限，并启动服务")
    except subprocess.CalledProcessError:
        logger.info(traceback.format_exc())

    try:
        adb_shell = subprocess.Popen(f'{adb_path} shell', stdin=subprocess.PIPE, shell=True)
        adb_shell.communicate(b'su\npkill -f hluda\nchmod 755 /data/local/tmp/hluda\n/data/local/tmp/hluda &\n',
                              timeout=5)
    except subprocess.TimeoutExpired:
        adb_shell.kill()
        logger.info("启动服务成功")
        logger.info("在命令行中使用frida-ps -U -ai测试你的环境是否成功了吧")
    except Exception:
        logger.error(f"启动失败,{traceback.format_exc()}")


def get_python_version():
    python_version = sys.version_info
    py3 = six.PY3
    if py3:
        if python_version < (3, 6):
            logger.warning("如果出现问题请尝试使用Python3.6以上版本")
    else:
        raise IsNotPython3

def get_hluda_server():
    """
    自动辨别cpu架构类型
    :return:
    """
    file_name="hluda"
    cpu_version = get_cpu_version()
    prefix_url = "https://github.com/hluwa/strongR-frida-android/releases/download/14.2.18/hluda-server-14.2.18-android-{}"
    if "arm64" in cpu_version:
        url = prefix_url.format("arm64")
    elif "armeabi" in cpu_version:
        url = prefix_url.format("arm")
    else:
        url = prefix_url.format(cpu_version)

    frida_full_path = os.path.join(frida_server_path, file_name)
    logger.info(f"开始下载hluda-server 版本--{cpu_version}")

    download_from_url(url, dst=frida_full_path)
    logger.info(f"下载hluda-server 成功！,文件位置:{frida_full_path}")

    adb_operation(frida_full_path)

def get_cpu_version():
    command = f"{adb_path} shell getprop ro.product.cpu.abi"
    complete = subprocess.run(command, check=True, shell=True,
                              stdout=subprocess.PIPE)
    code = complete.returncode
    if code == 0:
        result = complete.stdout.decode("utf-8")
    return result


def main():
    get_python_version()
    install_list = ["frida==14.2.2", "frida-tools==9.1.0", "objection==1.9.6"]
    python_path = sys.executable
    for install_item in install_list:
        logger.info(f"当前安装的是:{install_item.split('==')[0]}")

        try:
            command = f'{python_path} -m pip install {install_item}'
            completed = subprocess.run(command, check=True, shell=True,
                                       stdout=subprocess.PIPE)
            result = completed.stdout.decode("utf-8")
            logger.info(result)
        except subprocess.CalledProcessError:
            raise ValueError(f"{install_item},安装失败")
    get_hluda_server()


if __name__ == '__main__':
    main()
