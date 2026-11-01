import tkinter as tk
from tkinter import messagebox, filedialog
from services import MusicService

class Playwindow(tk.Tk):            #tk.Tk：是 tkinter 模块里的一个类。Tk 代表主窗口（Top-level window）
    def __init__(self,ser: MusicService):
        super().__init__()          # 初始化父类（也就是创建窗口）,相当于真正把底层的窗口系统建出来。
        self.service = ser          # 把业务逻辑实例存起来（组合）
        self.title('Local MusicBox')        # 调用父类方法，设置窗口标题
        self.geometry('600x400+300+200')         # geometry 是 Tkinter 从底层 Tcl/Tk 脚本语言继承过来的方法，它接受一个特定格式的尺寸描述字符串，标准语法格式为："宽度x高度+左边距+上边距"（中间是小写字母 x）。
        # 创建控件,self 代表把按钮嵌在这个窗口里 (直接使用 command 绑定处理函数，无需额外的 bind)
        self.btn_play = tk.Button(self, text = 'play', command=self.do_play)
        self.btn_import = tk.Button(self, text = 'Import Music', command=self.do_import)
        self.btn_delete = tk.Button(self, text = 'Delete', command=self.do_delete)
        self.listbox = tk.Listbox(self, width=80, height=15)            # 创建列表框
        # 布局(Grid Layout)
        self.btn_play.grid(row=0, column=0, padx=5, pady=5)
        self.btn_import.grid(row=0, column=1, padx=5, pady=5)
        self.btn_delete.grid(row=0, column=2, padx=5, pady=5)
        self.listbox.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
        self.refresh_list()         # 窗口画完后，立刻去读数据库，把数据填到列表里

    def refresh_list(self):
        '''Read data from the database and refresh it on the interface.'''
        self.listbox.delete(0, tk.END)          # clear old list
        try:
            songs = self.service.get_all_music()
            for song in songs:
                name = song['name'] if isinstance(song, dict) else song[1]              #三元运算符（Ternary Operator）
                singer = song['singer'] if isinstance(song, dict) else song[2]
                display_text = f"{name} - {singer}"
                self.listbox.insert(tk.END, display_text)
        except Exception as e:
            print("Failed to load the list:", e)

    def do_play(self):
        '''Click the Play button to trigger.'''
        # Get the item the user selected from the list
        select_index = self.listbox.curselection()
        if not select_index:
            messagebox.showwarning('Tips:', 'please select one song!')
            return
        selected_text = self.listbox.get(select_index[0])           #传入索引数字（如 0），返回该行在界面上渲染显示的字符串内容。
        music_name = selected_text.split(' - ')[0]  # Extract the music name from the display text
        print(f'ready to play:{music_name}')
        self.service.play_music(music_name)

    def do_import(self):
        print('ready to import music')
        file_path = filedialog.askopenfilename(
            title='select music file',
            filetypes=[('MP3 Files', '*.mp3'),('flac','.flac')]
        )           #接收一个元组列表，如 [('描述文本', '*.后缀')]，用于限制用户在文件弹窗中能够选择的文件类型。
        if file_path:
            if hasattr(self.service, 'add_music'):
                self.service.add_music(file_path)
            self.refresh_list()

    def do_delete(self):
        selected_index = self.listbox.curselection()            #返回的是一个包含当前选中项索引的元组
        if not selected_index:
            messagebox.showwarning('Tips', 'please select the song need delete!')
            return
        selected_text = self.listbox.get(selected_index[0])
        music_name = selected_text.split(' - ')[0]  # Extract the music name from the display text
        print(f'Ready to delete: {music_name}')
        success = self.service.delete_music(music_name)
        if success:
            messagebox.showinfo('Success', f'Song "{music_name}" deleted successfully!')
        else:
            messagebox.showerror('Error', f'Failed to delete song "{music_name}".')
        self.refresh_list()



if __name__ == '__main__':
    service = MusicService()
    # 模拟登录一个测试账号，确保 service.user 有值
    service.login("test_user", "123456")
    app = Playwindow(service)
    app.mainloop()
