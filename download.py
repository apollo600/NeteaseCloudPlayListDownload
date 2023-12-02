'''
Author: mxy 1356464784@qq.com
Date: 2023-12-02 18:21:02
LastEditors: mxy 1356464784@qq.com
LastEditTime: 2023-12-02 21:39:54
FilePath: /NeteaseCloudPlayListDownload/download.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
'''
1. 
'''

from login import UserConfig
import requests
import json
import concurrent.futures
import time
import os


def getListDetail(host, header, cookie, id):
    max_try = 10

    for i in range(max_try):
        try:
            url = host + "/playlist/detail?id=" + str(id)
            print("获取歌单信息中...")
            response = requests.get(url, headers=header, cookies=cookie)
            json_obj = json.loads(response.text)
            if json_obj["code"] == 200:
                j = json_obj["playlist"]
            else:
                print("歌单获取失败，请检查您输入的歌单id")
                exit
            print("获取歌单信息成功")
            return j
        except:
            continue


# 获取歌单所有歌曲id,返回 列表 一系列id
def getListId(j):
    l = []
    trackIds = j["trackIds"]
    for ids in trackIds:
        l.append(ids["id"])
    return l


# 获取音乐真实下载地址
def getMusicUrl(host, header, cookie, id):
    url = host + "/song/url?id=" + str(id)
    response = requests.get(url, headers=header, cookies=cookie)
    json_obj = json.loads(response.text)
    return json_obj["data"][0]["url"]


def getMusicDetail(host, header, cookie, id):
    url = host + "/song/detail?ids=" + str(id)
    print(f"获取音乐 {id} 信息中...")
    try:
        response = requests.get(url, headers=header, cookies=cookie)
        json_obj = json.loads(response.text)
        data = {}
        if len(json_obj["songs"]) > 0:
            data["title"] = json_obj["songs"][0]["name"]  # 获得歌曲名字
            data["img_url"] = json_obj["songs"][0]["al"]["picUrl"]  # 获得专辑封面
            # 循环获得作者,拼接字符串
            s = ""
            for au in json_obj["songs"][0]["ar"]:
                s += au["name"] + ","
            data["artist"] = s
            data["album"] = json_obj["songs"][0]["al"]["name"]  # 获得专辑名字
        else:
            pass

        download_url = getMusicUrl(host, header, cookie, id)
        data["url"] = download_url
        data['id'] = id
        return data
    except Exception as e:
        print(f"获取音乐 {id} 失败: {e}")


def ReplaceName(str):
    sets = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in str:
        if char in sets:
            str = str.replace(char, '')
    return str


def downloadMusic(header, cookie, down, root):
    print(f"{down['id']} 下载中......")
    
    os.makedirs(root, exist_ok=True)
    
    if not down["title"] or not down["url"]:
        raise RuntimeError("数据不完整")
    
    max_tries = 10
    fail_times = 0
    
    while fail_times < max_tries:
        music_url = down["url"]
        music_name = down["title"]
        down_path = os.path.join(root, ReplaceName(
            music_name).strip()) + ".mp3"  # 歌曲路径
        try:
            resp = requests.get(music_url, cookies=cookie, headers=header)
            with open(down_path, "wb") as f:
                f.write(resp.content)
            print(f'已完成 {music_name} 歌曲下载')
            break
        except Exception as e:
            print(f"重试 {music_name} 第 {fail_times} 次 {e}")
            fail_times += 1
            continue


def getDownloadList(host, header, cookie, id):
    j = getListDetail(host, header, cookie, id)
    music_ids = getListId(j)

    for music_id in music_ids:
        yield music_id


if __name__ == "__main__":
    id = 5173444095
    config = UserConfig("./config.toml")

    j = getListDetail(config.host, config.header, config.cookie, id)
    ids = getListId(j)

    for music in getMusicDetail(config.host, config.header, config.cookie,
                                ids):
        print(music)
