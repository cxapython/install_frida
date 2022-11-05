# install_frida
installation of specific versions of frida, frida-server and objection environment
### Adapt to different cpu architectures
includes:
- arm64
- arm
- x86
- x86_64
### Python Version
```>3.6```

### Install dependencies
```

 python3.6 -m pip install six requests tqdm loguru  -i https://mirrors.ustc.edu.cn/pypi/web/simple
```
### How To Run
```
git clone https://github.com/cxapython/install_frida.git
cd install_frida
python3 main.py
```
### Thanks
frida
https://github.com/frida/frida

objection
https://github.com/sensepost/objection

strongR-frida-android(hluda)
https://github.com/hluwa/strongR-frida-android
