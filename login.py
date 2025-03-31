'''
Author: mxy 1356464784@qq.com
Date: 2023-12-02 15:55:18
LastEditors: mxy 1356464784@qq.com
LastEditTime: 2023-12-04 18:41:46
FilePath: /NeteaseCloudPlayListDownload/login.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import toml
import time
import requests
import json


class UserConfig:

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self):
        config_path = self.config_path
        try:
            _config = toml.load(config_path)
        except TypeError as e:
            print("配置文件路径错误:", config_path)
            print(e)
            exit
        except toml.TomlDecodeError as e:
            print("配置文件格式错误:", config_path)
            print(e)
            exit

        return _config

    def save_config(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            toml.dump(self._config, f)

    def __getattr__(self, key):
        if key == 'keys':
            return self._config.keys()
        return self._config.get(key)

    def __setattr__(self, key, value):
        # 避免递归调用
        if key in ['_config', 'config_path']:
            super().__setattr__(key, value)
        else:
            self._config[key] = value
            self.save_config()


def checkLogin(config: UserConfig) -> bool:
    if 'cookie' in config.keys:
        cookies = config.cookie
        if confirmCookie(cookies, config.host, config.header):
            return True

    return False


def login(config: UserConfig) -> None:
    print("您是否要登录？（非常建议您登录，不登录极大可能出错；而且考虑到安全性，目前仅支持二维码登录）")
    user_input = input("请输入'y'或者'n'（y表示同意登录，n表示不登录）")
    while True:
        if user_input == 'y':
            cook = loginByQR(config)
            if cook == "":
                raise RuntimeError("登录失败")
            else:
                config.cookie = getCookieDict(cook)
                return
        else:
            user_input = input("请输入'y'或者'n'（y表示同意登录，n表示不登录）")
            continue


def loginByQR(config: UserConfig) -> str:
    import base64
    import skimage.io
    import cv2
    
    cookie_str = ""
    host = config.host
    header = config.header

    # 获取二维码key
    url = host + '/login/qr/key'
    data = {"timestamp": time.time()}
    print("获取二维码key中...")
    response = requests.post(url, data=data, headers=header)
    re_json = response.json()
    key = re_json["data"].get("unikey")  # 获取二维码key

    # 获取二维码图片
    url = host + '/login/qr/create'
    data = {"timestamp": time.time(), "key": key, "qrimg": "true"}
    print(f"获取二维码中...{key}")
    response = requests.post(url, data=data, headers=header)
    re_json = response.json()
    qrimg = re_json["data"]["qrimg"]
    base64_str = qrimg.split(",")[1]
    
    # 显示二维码图像
    imgdata = base64.b64decode(base64_str)  # 对base64字符串解码成二进制图像代码
    img = skimage.io.imread(imgdata, plugin='imageio')
    cv2.imshow("关闭二维码窗口将会自动检查登录", img)
    cv2.waitKey(0)
    
    # 获取用户扫描二维码状态
    url = host + '/login/qr/check'
    data = {"key": key}
    print("检查登录中...")
    response = requests.post(url, data=data)
    re_json = response.json()
    # print(re_json)
    if re_json["code"] == 803:
        print("登录成功")
        cookie_str = re_json["cookie"]
    else:
        print("登录异常")
        exit()  # 退出主程序
    
    # 返回数据
    return cookie_str


def getCookieDict(cook):
    '''将cookie字符串格式化为字典型变量
    '''
    cookies = {}  # 初始化cookies字典变量
    for line in cook.split(';'):  # 按照字符：进行划分读取
        # 其设置为1就会把字符串拆分成2份
        if line != "":
            # print(line)
            if "=" in line:
                name, value = line.strip().split('=')
                cookies[name] = value  # 为字典cookies添加内容
    return cookies


def confirmCookie(cookies, host, header):
    fail_times = 0
    max_tries = 10
    
    while fail_times < max_tries:
        try:
            # 获取登录状态
            t = int(time.time())
            url = host + "/login/status?timestamp=" + str(t)
            print("获取登录状态中...")
            response = requests.get(url, headers=header, cookies=cookies)
            break
        except Exception as e:
            fail_times += 1
            print(f"重试第 {fail_times} 次: {e}")
    
    json_obj = json.loads(response.text)
    # print(response.text)
    try:
        nickname = json_obj["data"]["profile"]["nickname"]
    except:
        return False
    
    print(f"欢迎您：{nickname}")
    if json_obj["data"]["account"] == None:
        return False
    else:
        return True
    

if __name__ == '__main__':
    config = UserConfig("./config.toml")
    if not config:
        print("配置文件打开失败")
    
    if not checkLogin(config):
        try:
            login(config)
        except RuntimeError as e:
            print(e)
            exit
    else:
        print("已登录")
