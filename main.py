from login import UserConfig, checkLogin, login
from db import create_download_list_database, check_id_exists, insert_download_list_database
from download import getDownloadList, downloadMusic, getMusicDetail

import time


def main(folder_path, db_path):
    # 登录
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
        
    # 获取歌单信息
    count = 0
    create_download_list_database(db_path)
    max_tries = 10
    fail_times = 0
    
    for music_id in getDownloadList(config.host, config.header, config.cookie, id=config.id):
        if check_id_exists(db_path, "download_list", "music_id", music_id):
            print(f"已存在 {music_id}")
            count += 1
            continue

        while fail_times < max_tries:
            down = getMusicDetail(config.host, config.header, config.cookie, music_id)
            if down is not None:
                print(count, down)
                
                if downloadMusic(config.header, config.cookie, down, folder_path):
                    count += 1
                    insert_download_list_database(down, db_path)

                # next
                fail_times = 0
                break
            else:
                fail_times += 1
                print(f"重试 {music_id} 第 {fail_times} 次")
                time.sleep(2)


# 初始化，检查目录
def init():
    #读取配置文件name，password，cookie
    if not os.path.exists(config_):
        w= open(config_,"w")
        w.write('{}')
        w.close()
    # 创建默认下载目录
    if not os.path.isdir("MusicDownLoad"):
        os.makedirs("MusicDownLoad")

    def l():
            # 是否要登录？
            print("您是否要登录？（非常建议您登录，不登录极大可能出错；而且考虑到安全性，目前仅支持二维码登录）")
            user_input=input("请输入'y'或者'n'（y表示同意登录，n表示不登录）")
            if user_input=='y':
                cook=loginByQR()
                user_json["cookie"]=cook
                # 存储cookie到用户JSON文件
                f=open(config_,"w")
                f.write(json.dumps(user_json))
                f.close()
            else :
                cookie={}
    
    # 验证用户JSON文件中的cookie是否可用，不可用就让用户选择是否登录
    with open(config_,"r") as fop:
        config_text=fop.read()
        user_json=json.loads(config_text)
        if "cookie" in user_json.keys():
            # print("有cookie")
            config_cookie=user_json["cookie"]
            cookie=getCookieDict(config_cookie)
            if confirmCookie(cookie):
                print("自动登录成功")
            else:
                l()
        else:
            # print("无cookie")
            l()


# 获取歌单详情(包括介绍，名字等等)
def getListDetail(ids,cookie):
    url=host+"/playlist/detail?id="+str(ids)
    response = requests.get(url,headers=header,cookies=cookie)
    json_obj=json.loads(response.text)
    if json_obj["code"]==200:
        j=json_obj["playlist"]
    else:
        print("歌单获取失败，请检查您输入的歌单id")
        sys.exit()
    return j


# 获取歌单所有歌曲id,返回 列表 一系列id
def getListId(j):
    l=[]
    trackIds=j["trackIds"]
    for ids in trackIds :
        #print(ids["id"])
        l.append(ids["id"])
    return l


# 获取音乐真实下载地址
def getMusicUrl(id,cookie):
    url=host+"/song/url?id="+str(id)
    response = requests.get(url,headers=header,cookies=cookie)
    json_obj=json.loads(response.text)
    return json_obj["data"][0]["url"]


# 打包歌单的歌曲下载链接、歌名等，返回的是json数组对象 # 过程时间比较长，需要进度条
def publishDownLoad(ids,cookie) :
    downl=[]

    with tqdm(total=len(ids), desc='进度') as bar:
        t=0
        for i in ids:
            t+=1
            #print("正在处理："+str(i))
            music={}
            music["url"]=getMusicUrl(i,cookie)
            detail=getMusicDetail(i,cookie)
            if detail!={}:
                music["name"]=detail["name"]
                music["author"]=detail["author"]
                music["album"]=detail["album"]
                music["imgUrl"]=detail["imgUrl"]
            else:
                print("歌曲获取失败")
            downl.append(music.copy())
            music.clear()
            bar.update(1)

        # 导出下载链接
        file=open("download_link.json","w")
        file.write(json.dumps(downl))
        file.close()
        # bar.update(t+1)
    print("资源整合成功，下载链接已导出,开始下载歌曲")
    return downl


def Download(dl,file):# 由此方法判断选择那种方法下载
    path=""
    if file=="":
        path=os.getcwd()+"\\MusicDownLoad"
    else:
        path=file
    print(path)
    if input("下载方式选择：0,1（0是选择普通下载;1是IDM下载）")=="1":
        IDMdownload(dl,path)
    else:
        Comdownload(dl,path)


def Comdownload(dl,file):
    print("普通下载中......")
    down_playlist_dir = file+"\\"+ReplaceName(playlistName).strip() # 下载存储位置
    # 建立文件夹
    if os.path.exists(down_playlist_dir):
        pass
    else:
        os.mkdir(down_playlist_dir)
    for info in dl:
        if not info.get("name") or not info.get("url"):
            break
        music_url=info["url"]
        music_name=info["name"]
        down_path=down_playlist_dir+"\\"+ReplaceName(music_name).strip()+".mp3" # 歌曲路径
        try:
            resp=requests.get(music_url,cookies=cookie,headers=header)
            with open(down_path,"wb") as f:
                f.write(resp.content)
            print(f'已完成《{music_name}》歌曲下载')
        except Exception as e:
            print(f"歌曲《{music_name}》下载失败")
    pass


def IDMdownload(dl:list,file:str):# dl参数是列表，每个列表项为字典
    idm_path=input("请输入idm软件存放地点，直接回车将使用默认路径")
    if idm_path=="":
        IDM = 'C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe'
    else:
        IDM=idm_path
    if os.path.exists(IDM):
        print("idm下载中......")
        down_path = file+"\\"+ReplaceName(playlistName).strip()
        # 建立文件夹
        if os.path.exists(down_path):
            pass
        else:
            os.mkdir(down_path)
        for i in dl:
            if i["url"]!=None:
                down_url = i["url"]
                str=i["name"]
                name=ReplaceName(str)
                output_filename=name.strip()+".mp3"
                call([IDM, '/d',down_url, '/p',down_path, '/f', output_filename, '/n', '/a'])
        print("idm正在下载，请打开idm查看下载进度")
    else:
        print("IDM程序不存在，将使用普通下载")
        Comdownload(dl,file)


def ReplaceName(str):
    sets = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in str:
        if char in sets:
            str = str.replace(char, '')
    return str


if __name__ == '__main__':
    main("/Users/sekiro/Downloads/Sekiro's Music", "./mp3_database.sqlite")
    
    # cookie={}       # 全局变量
    # playlistName="" # 全局变量
    # print("欢迎使用网易云歌单音乐批量导出工具")
    # init()

    # # 本地音乐库扫描

    # # 本地数据库扫描
    #     # 检测本地数mp3元数据是否完整，如果不完整尝试完善

    # # 歌单下载
    # ids=input("请输入您要下载的歌单id\n\r")
    # try:
    #     play_list=getListDetail(ids=int(ids),cookie=cookie)
    #     print("歌单名称："+play_list["name"])
    #     playlistName=play_list["name"]
    #     print("歌单里歌曲的数量："+str(play_list["trackCount"]))
    #     musics=getListId(play_list)
    #     download=publishDownLoad(musics,cookie)
    # except :
    #     print("资源整合出错！")
    #     print(traceback.format_exc())
    #     sys.exit()
    # if input("是否下载歌曲？（y/n）")=="n":
    #     sys.exit()
    # file_path=input("请输入歌曲保存路径，直接回车，将会保存在默认路径")
    # if file_path!="" and os.path.exists(file_path):
    #     Download(download,file_path)
    # elif file_path=="":
    #     Download(download,"")
    # else :
    #     print("您输入的文件目录不存在,将保存在默认目录下")
    #     Download(download,"")

    # # 退出确认
    # while True:
    #     exit_confirm=input("程序运行结束，输入q退出")
    #     if exit_confirm=="q":
    #         exit()
    #     else :
    #         continue
