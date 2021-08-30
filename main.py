# -*- coding: utf-8 -*-
# @时间 : 2020/10/28 10:48 下午
# @作者 : 陈祥安
# @文件名 : install_frida.py
# @公众号: Python学习开发

import lzma
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
frida_server_path = os.path.join(_temp, "fs1280")
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
    logger.info("frida-server安装到手机")
    try:
        adb_shell = subprocess.run(f'{adb_path} push {fs_file} /data/local/tmp', check=True, shell=True,
                                   stdout=subprocess.PIPE)
        logger.info(adb_shell.stdout.decode("utf-8"))
        logger.info("安装成功，准备修改权限，并启动服务")
    except subprocess.CalledProcessError:
        logger.info(traceback.format_exc())

    try:
        adb_shell = subprocess.Popen(f'{adb_path} shell', stdin=subprocess.PIPE, shell=True)
        adb_shell.communicate(b'su\npkill -f fs1280\nchmod 755 /data/local/tmp/fs1280\n/data/local/tmp/fs1280 &\n',
                              timeout=5)
    except subprocess.TimeoutExpired:
        adb_shell.kill()
        logger.info("启动服务成功")
    except Exception:
        logger.error(f"启动失败,{traceback.format_exc()}")


def get_python_version():
    python_version = sys.version_info
    py3 = six.PY3
    if py3:
        if python_version > (3, 6) and python_version < (3, 7):
            logger.info("完美的python3.6环境")
        else:
            logger.warning("如果出现问题请尝试使用Python3.6")
    else:
        raise IsNotPython3


def decompress_file(input_xz_file):
    logger.info("开始解压fs1280.xz文件")
    output_file = input_xz_file.replace(".xz", "")
    try:
        with lzma.open(input_xz_file, 'rb') as _input:
            with open(output_file, 'wb') as output:
                shutil.copyfileobj(_input, output)
    except Exception:
        output_file = ""
    return output_file


def get_frida_server():
    """
    自动辨别cpu架构类型
    :return:
    """
    file_name = "fs1280.xz"
    cpu_version = get_cpu_version()
    prefix_url = "https://github.com/frida/frida/releases/download/12.8.0/frida-server-12.8.0-android-{}.xz"
    if "arm64" in cpu_version:
        url = prefix_url.format("arm64")
    elif "armeabi" in cpu_version:
        url = prefix_url.format("arm")
    else:
        url = prefix_url.format(cpu_version)

    frida_full_path = os.path.join(frida_server_path, file_name)
    logger.info(f"开始下载frida-server 版本--{cpu_version}")

    download_from_url(url, dst=frida_full_path)
    logger.info(f"下载frida-server成功！,文件位置:{frida_full_path}")
    out_file_path = decompress_file(frida_full_path)
    if out_file_path:
        logger.info("解压文件成功")

    adb_operation(out_file_path)


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
    install_list = ["frida==12.8.0", "frida-tools==5.3.0", "objection==1.8.4"]
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
    get_frida_server()


if __name__ == '__main__':
    main()