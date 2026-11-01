import bcrypt
from dbutil_m import DB_util_m
import pygame
import os

class MusicService:
    def __init__(self):
        self.user = None            # 保存当前登录用户的信息 (字典格式)
        pygame.mixer.init()         # 音频混音器初始化 在类初始化（__init__）或程序启动时调用一次即可，反复调用会消耗性能甚至引发报错

    def register(self, uname:str, password:str) -> bool:
        '''
        Registration process:
        Convert the plaintext password into a hash,
        store it in the database
        '''
        # Convert to bytes, generate salt, compute hash, then back to str
        hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        hashed_str = hashed_bytes.decode('utf-8')
        # Insert info
        sql = "INSERT INTO `user` (uname, password_hash) VALUES (%s, %s)"
        # Instantiate utility class
        db = DB_util_m()
        try:
            success = db.execute_dml(sql, uname, hashed_str)
            if success:
                print(f'User {uname} registration successful!')
                return True
            else:
                print(f'User {uname} registration failed.')
                return False
        finally:
            db.close()

    def login(self, uname:str,password:str) -> bool:
        sql = 'select id, uname, password_hash from `user` where uname=%s'
        db = DB_util_m()
        try:
            user = db.query_one(sql, uname)
            if not user:
                print('Login failed: User not exists.')
                return False

            stored_hash  = user['password_hash']

            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                print('Login successful!')
                self.user = user
                return True
            else:
                print('Login failed.')
                return False
        finally:
            db.close()

    def get_all_music(self) -> list:
        '''Get all the music in the database for display on the interface.'''
        sql = 'SELECT id, name, singer, path FROM music'
        db = DB_util_m()
        try:
            return list(db.query_all(sql))     #query_all 返回的是列表，里面每个元素是个字典
        finally:
            db.close()

    def play_music(self, music_name:str):
        '''Play the music with the given name.'''
        if not self.user:
            print('Please login first!')
            return
        sql = '''
                SELECT m.path
                FROM play_list p
                LEFT JOIN music m on p.m_id = m.id
                WHERE p.u_id=%s and m.name=%s
            '''
        db = DB_util_m()
        try:
            result = db.query_one(sql, self.user['id'], music_name)
            if result and result.get('path'):         #result：确保 SQL 确实查到了记录（不是 None）。result.get('path')：安全提取字典中的 path 属性。即便 path 为 None 或空字符串，它也能自动判定为 False，有效拦截无效路径。
                pygame.mixer.music.load(result['path'])  #加载音频文件
                pygame.mixer.music.play()               #开始播放
                print(f'Playing music: {music_name}')
            else:
                print(f'No music found with name: {music_name}')
        finally:
            db.close()

    def delete_music(self, music_name:str) -> bool:
        '''Delete the music with the given name from the database.'''
        if not self.user:
            print('Please login first!')
            return False
        sql = '''
            DELETE FROM play_list
            WHERE u_id=%s AND m_id = (SELECT id FROM music WHERE name=%s LIMIT 1)
            '''
        db = DB_util_m()
        try:
            success = db.execute_dml(sql, self.user['id'], music_name)
            if success:
                print(f'Music {music_name} deleted successfully.')
                return True
            else:
                print(f'Failed to delete music {music_name}.')
                return False
        finally:
            db.close()

    def add_music(self, file_path:str) -> bool:
        '''Add a new music file to the database.'''
        if not os.path.exists(file_path):
            print(f'File does not exist: {file_path}')
            return False
        file_name = os.path.basename(file_path)         #从完整路径中剥离出文件名
        music_name = os.path.splitext(file_name)[0]     #拆分文件名与后缀，返回元组

        # 将路径统一转为正斜杠 /，防止 Windows 下路径反斜杠报错
        clean_path = file_path.replace("\\", "/")
        db = DB_util_m()
        try:
        # 2. 检查曲库中是否已经存在该路径的歌曲（防止重复导入）
            check_sql = "SELECT id FROM music WHERE path = %s"
            existing = db.query_one(check_sql, clean_path)

            if existing:
                # 如果是字典取 'id'，元组取 [0]
                m_id = existing['id'] if isinstance(existing, dict) else existing[0]
                print(f"歌曲已存在于曲库中，ID: {m_id}")
            else:
                # 插入新歌曲到 music 表（歌手默认为 "未知歌手"）
                insert_music_sql = "INSERT INTO music (name, singer, path) VALUES (%s, %s, %s)"
                db.execute_dml(insert_music_sql, music_name, "未知歌手", clean_path)

                # 重新获取刚刚插入的音乐 ID
                new_song = db.query_one(check_sql, clean_path)
                if not new_song:
                    raise ValueError(f"无法获取新歌曲 ID: {music_name}")
                m_id = new_song['id'] if isinstance(new_song, dict) else new_song[0]
                print(f"新歌曲入库成功: {music_name}")

            # 3. 将歌曲关联到当前登录用户的播放列表 (play_list) 中
            if self.user:
                user_id = self.user['id'] if isinstance(self.user, dict) else self.user[0]

                # 检查用户的播放列表是否已包含该歌
                check_playlist = "SELECT * FROM play_list WHERE u_id = %s AND m_id = %s"
                if not db.query_one(check_playlist, user_id, m_id):
                    insert_playlist_sql = "INSERT INTO play_list (u_id, m_id) VALUES (%s, %s)"
                    db.execute_dml(insert_playlist_sql, user_id, m_id)
                    print(f"已将 {music_name} 添加到用户播放列表")

            return True
        except Exception as e:
            print(f"导入音乐失败: {e}")
            return False
        finally:
            db.close()



if __name__ == '__main__':
    import time

    service = MusicService()

    # 0. 先向数据库写一首测试音乐数据
    db_init = DB_util_m()
    try:
        # 如果没有《晴天》，先插一条模拟音乐
        check_music = db_init.query_one("SELECT id FROM music WHERE name = %s", "晴天")
        if not check_music:
            db_init.execute_dml(
                "INSERT INTO music (name, singer, path) VALUES (%s, %s, %s)",
                "晴天", "周杰伦", "music_files/晴天.mp3"
            )
            print("--- 初始化数据：添加测试歌曲《晴天》成功 ---")
    finally:
        db_init.close()

    print("\n--- 1. 测试注册功能 ---")
    # 使用动态账号，解决 Duplicate entry 唯一性约束报错
    test_user = f"dev_{int(time.time())}"
    test_pass = "123456"
    reg_success = service.register(test_user, test_pass)
    print(f"注册测试结果: {reg_success}")

    print("\n--- 2. 测试登录功能 ---")
    login_success = service.login(test_user, test_pass)
    print(f"正确密码登录测试结果: {login_success}")

    print("\n--- 3. 测试获取全量曲库 ---")
    songs = service.get_all_music()
    print(f"查到的歌曲列表: {songs}")

    # 给当前登录用户的 play_list 增加这首歌曲关联，以便测试播放与删除
    if service.user and songs:
        db_link = DB_util_m()
        try:
            m_id = songs[0]['id'] if isinstance(songs[0], dict) else songs[0][0]
            db_link.execute_dml(
                "INSERT INTO play_list (u_id, m_id) VALUES (%s, %s)",
                service.user['id'] if isinstance(service.user, dict) else service.user[0],
                m_id
            )
        finally:
            db_link.close()

    print("\n--- 4. 测试音乐播放 ---")
    service.play_music("晴天")

    print("\n--- 5. 测试删除播放列表歌曲 ---")
    del_success = service.delete_music("晴天")
    print(f"删除测试结果: {del_success}")

