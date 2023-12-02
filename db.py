'''
Author: mxy 1356464784@qq.com
Date: 2023-12-02 17:20:52
LastEditors: mxy 1356464784@qq.com
LastEditTime: 2023-12-02 21:48:37
FilePath: /NeteaseCloudPlayListDownload/db.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import os
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from mutagen.mp3 import MP3
import sqlite3
from download import getDownloadList, getMusicDetail, downloadMusic
from login import UserConfig
import asyncio

# 遍历指定文件夹中的所有 MP3 文件
def get_mp3_files(folder_path):
    mp3_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".mp3"):
                mp3_files.append(os.path.join(root, file))
    return mp3_files

# 读取 MP3 文件的元数据
def get_metadata(file_path):
    try:
        audio = MP3(file_path)
        audio.pprint()
        # print(dir(audio))
        # return {
        #     "title": audio['TIT2'],
        #     "artist": audio['TPE1'],
        #     "album": audio['TALB'],
        #     "year": audio.date,
        #     "genre": audio.genre,
        #     "duration": audio.duration_seconds,  # Convert duration to seconds
        # }
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return None

# 创建 SQLite 数据库并保存元数据
def create_mp3_database(mp3_files, database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # 创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mp3_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            artist TEXT,
            album TEXT,
            duration REAL,
            file_size INTEGER
        )
    ''')

    # 插入数据
    for mp3_file in mp3_files:
        metadata = get_metadata(mp3_file)
        if metadata is not None:
            try:
                cursor.execute('''
                    INSERT INTO mp3_metadata (title, artist, album, duration, file_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (metadata["title"], metadata["artist"], metadata["album"], 
                    metadata["duration"], metadata["file_size"]))
            except sqlite3.OperationalError as e:
                print("数据库信息不匹配，请删除数据库文件后重新运行程序")
                print(e)
                exit
                

    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    
def create_download_list_database(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS download_list (
            music_id INTEGER PRIMARY KEY,
            title TEXT,
            artist TEXT,
            album TEXT,
            url TEXT,
            img_URL TEXT
        )
    ''')
    print("创建数据库 download_list 成功")
    
    # 提交更改并关闭连接
    conn.commit()
    conn.close()
    

def insert_download_list_database(down, database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
                    INSERT OR REPLACE INTO download_list (music_id, title, artist, album, url, img_URL)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (down['id'], down['title'], down['artist'], down['album'], 
                          down['url'], down['img_url']))
        print(f"插入 {down['title']} 成功")
    except sqlite3.Error as e:
        print(f"插入 {down['title']} 失败 {e}")
        exit
        
    # 提交更改并关闭连接
    conn.commit()
    conn.close()


def check_id_exists(db_path, table_name, column_name, target_id):
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询是否存在特定的 ID
    query = f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} = ?"
    cursor.execute(query, (target_id,))
    result = cursor.fetchone()[0]

    # 关闭数据库连接
    conn.close()

    # 如果结果大于 0，表示存在该 ID，否则不存在
    return result > 0


async def download_and_insert(config, down, folder_path, database_path):
    loop = asyncio.get_event_loop()

    def download_task():
        err = downloadMusic(config.header, config.cookie, down, folder_path)
        if err:
            insert_download_list_database(down, database_path)
        return err
    
    # 在当前线程中异步执行下载任务
    result = await loop.run_in_executor(None, download_task)
    return result


async def main():
    folder_path = "/Users/sekiro/Downloads/Sekiro's Music"  # 替换成你的本地文件夹路径
    database_path = "./mp3_database.sqlite"  
    
    config = UserConfig("./config.toml")
    count = 0
    create_download_list_database(database_path)
    
    download_tasks = []
    max_tries = 10
    fail_times = 0
    
    for music_id in getDownloadList(config.host, config.header, config.cookie, id=5173444095):
        if count > 2:
            break
        
        if check_id_exists(database_path, "download_list", "music_id", music_id):
            print(f"已存在 {music_id}")
            count += 1
            continue

        while fail_times < max_tries:
            down = getMusicDetail(config.host, config.header, config.cookie, music_id)
            if down is not None:
                print(count, down)
                count += 1
                
                # download in a new thread
                download_task = asyncio.create_task(download_and_insert(config, down, folder_path, database_path))
                download_tasks.append(download_task)

                # next
                fail_times = 0
                break
            else:
                fail_times += 1
                print(f"重试 {music_id} 第 {fail_times} 次")

    # 等待所有下载任务完成，并获取结果
    results = await asyncio.gather(*download_tasks)
    print("Download results:", results)


if __name__ == "__main__":
    asyncio.run(main())

    # mp3_files = get_mp3_files(folder_path)
    # print(f"共找到 {len(mp3_files)} 个 MP3 文件")
    # create_database(mp3_files, database_path)
    
    # count = 0
    # for mp3_file in mp3_files:
    #     if get_metadata_mp3(mp3_file) is not None:
    #         count += 1
    # print(f"共找到 {count} 个 MP3 Metadata")
    
    # dict = get_metadata(mp3_files[0])
    # if dict is not None:
    #     print(dict)
