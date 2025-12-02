#!/usr/bin/env python
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import subprocess
import platform
from typing import Optional, Literal, TypedDict
from pathlib import Path

import ctypes
import sys

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # DPI
except: pass

# 隐藏控制台窗口（仅 Windows 有效）
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# 类型定义
class Shortcut(TypedDict):
    id: str
    type: Literal['URL', 'FILE', 'CMD']
    path: str
    run_count: int
    arguments: list[str]
    icon: str | None

class Config(TypedDict):
    shortcuts: list[Shortcut]

# 匹配算法
def id_match(id_part: Optional[str], id: str, ignore_case: bool = True) -> bool:
    """
    检查 id_part 是否是字符串 id 的非连续子串。
    
    :param id_part: 要检查的子串
    :param id: 原始字符串
    :param ignore_case: 是否忽视大小写
    :return: 如果 id_part 是 main 的非连续子串，返回 True；否则返回 False
    """
    if not id_part:
        return True
    if ignore_case:
        id = id.lower()
        id_part = id_part.lower()
    it = iter(id)  # 创建 main 的迭代器
    return all(char in it for char in id_part)

# 打开默认程序
def open_with_default(path: str):
    """使用默认程序打开文件或URL"""
    try:
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', path])
        else:  # Linux
            subprocess.run(['xdg-open', path])
    except Exception as e:
        messagebox.showerror("错误", f"无法打开路径: {e}")

def run_shortcut(shortcut: Shortcut, additional_arguments: list[str]):
    """运行快捷方式"""
    try:
        if shortcut['type'] in ('URL', 'FILE'):
            open_with_default(shortcut['path'])
        else:
            # 不等待进程退出
            args = [shortcut['path'], *shortcut['arguments'], *additional_arguments]
            if platform.system() == "Windows":
                subprocess.Popen(args, shell=True, start_new_session=True, creationflags=8)
            else:
                subprocess.Popen(args, shell=True, start_new_session=True)
        
        # 更新运行计数
        shortcut['run_count'] += 1
    except Exception as e:
        messagebox.showerror("错误", f"执行失败: {e}")

class ShortcutLauncher:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("快捷启动器")
        
        # 设置窗口位置和大小
        self.setup_window()
        
        # 加载配置
        self.config = self.load_config()
        self.shortcuts = self.config.get('shortcuts', [])
        
        # 当前显示的匹配结果
        self.matched_shortcuts = []
        self.selected_index = -1
        
        # 创建UI
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        # 初始显示所有快捷方式
        self.update_listbox("")
    
    def setup_window(self):
        """设置窗口属性"""
        # 设置窗口大小和位置
        window_width = 600
        window_height = 400
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口位置（居中）
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.resizable(True, True)
        
        # 设置窗口置顶
        self.root.attributes('-topmost', True)
        
        # 设置窗口样式
        style = ttk.Style()
        style.theme_use('clam')
    
    def config_location(self):
        if 'SM_CONF_LOCATION' in os.environ:
            target = Path(os.environ['SM_CONF_LOCATION'])
            target.parent.mkdir(exist_ok=True)
        else:
            target = Path(__file__).with_name('sm_config.json')
        return target

    def save_config(self, config: Config) -> Config:
        self.config_location().write_text(json.dumps(config, ensure_ascii=False, indent=4), 'utf-8')
    def default_config() -> Config:
        return {
            'shortcuts': []
        }

    def load_config(self) -> Config:
        if not self.config_location().exists():
            config = self.default_config()
            self.save_config(config)
            return config
        return json.loads(self.config_location().read_text(encoding='utf-8'))

    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入框
        input_label = ttk.Label(main_frame, text="输入快捷方式ID:", font=('Arial', 12))
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(main_frame, textvariable=self.input_var, font=('Arial', 14))
        self.input_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 结果列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 结果列表框
        self.listbox = tk.Listbox(
            list_frame, 
            font=('Arial', 11),
            yscrollcommand=scrollbar.set,
            selectbackground='#0078d4',
            selectforeground='white',
            activestyle='none',
            height=10
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.listbox.yview)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def bind_events(self):
        """绑定事件"""
        # 输入框事件
        self.input_var.trace('w', lambda *args: self.on_input_change())
        self.input_entry.bind('<Return>', lambda e: self.execute_selected())
        self.input_entry.bind('<Escape>', lambda e: self.root.destroy())
        
        # 列表框事件
        self.listbox.bind('<Double-Button-1>', lambda e: self.execute_selected())
        self.listbox.bind('<Return>', lambda e: self.execute_selected())
        self.listbox.bind('<ButtonRelease-1>', lambda e: self.on_listbox_click())
        
        # 键盘导航
        self.input_entry.bind('<Up>', lambda e: self.navigate_list(-1))
        self.input_entry.bind('<Down>', lambda e: self.navigate_list(1))
        self.listbox.bind('<Up>', lambda e: self.navigate_list(-1))
        self.listbox.bind('<Down>', lambda e: self.navigate_list(1))
        
        # 窗口事件
        self.root.bind('<Control-q>', lambda e: self.root.destroy())
        self.root.bind('<Control-w>', lambda e: self.root.destroy())
        
        # 设置焦点
        self.input_entry.focus_set()
    
    def on_input_change(self):
        """输入变化时的处理"""
        search_text = self.input_var.get().strip()
        self.update_listbox(search_text)
    
    def update_listbox(self, search_text: str):
        """更新列表显示"""
        # 清空列表
        self.listbox.delete(0, tk.END)
        self.matched_shortcuts = []
        
        # 筛选匹配的快捷方式
        for shortcut in self.shortcuts:
            if id_match(search_text, shortcut['id']):
                self.matched_shortcuts.append(shortcut)
                
                # 显示格式：id [类型] - path
                display_text = f"{shortcut['id']} [{shortcut['type']}] - {shortcut['path']}"
                if shortcut['run_count'] > 0:
                    display_text += f" (已运行{shortcut['run_count']}次)"
                
                self.listbox.insert(tk.END, display_text)
        
        # 更新状态栏
        count = len(self.matched_shortcuts)
        self.status_var.set(f"找到 {count} 个匹配项")
        
        # 如果有匹配项，默认选择第一个
        if self.matched_shortcuts:
            self.selected_index = 0
            self.listbox.selection_set(0)
            self.listbox.see(0)
        else:
            self.selected_index = -1
    
    def navigate_list(self, direction: int):
        """导航列表（上下键）"""
        if not self.matched_shortcuts:
            return
        
        # 计算新的索引
        new_index = self.selected_index + direction
        
        # 确保索引在有效范围内
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self.matched_shortcuts):
            new_index = len(self.matched_shortcuts) - 1
        
        # 更新选择
        self.selected_index = new_index
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(new_index)
        self.listbox.see(new_index)
        
        # 将焦点设置回输入框（为了继续输入）
        self.input_entry.focus_set()
    
    def on_listbox_click(self):
        """列表点击事件"""
        selection = self.listbox.curselection()
        if selection:
            self.selected_index = selection[0]
    
    def execute_selected(self):
        """执行选中的快捷方式"""
        if not self.matched_shortcuts or self.selected_index < 0:
            return
        
        if self.selected_index >= len(self.matched_shortcuts):
            return
        
        # 获取选中的快捷方式
        shortcut = self.matched_shortcuts[self.selected_index]
        
        # 获取输入框中的额外参数（如果有）
        input_text = self.input_var.get().strip()
        additional_args = []
        
        # 尝试从输入中提取额外参数（以空格分隔）
        if input_text:
            # 找到ID部分，剩余部分作为参数
            words = input_text.split()
            if words:
                # 第一个单词应该是ID或ID的一部分
                # 这里我们简单地将所有单词都作为参数，实际应用中可能需要更复杂的解析
                additional_args = words[1:] if len(words) > 1 else []
        
        try:
            # 执行快捷方式
            run_shortcut(shortcut, additional_args)
            
            # 更新状态栏
            self.status_var.set(f"已执行: {shortcut['id']}")
            
            # 清空输入框
            self.input_var.set("")
            self.update_listbox("")
            
            # 可选：几秒后自动关闭窗口
            self.root.after(0, self.root.destroy)
            
        except Exception as e:
            messagebox.showerror("执行错误", f"无法执行快捷方式: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    app = ShortcutLauncher(root)
    
    # 设置窗口关闭时的处理
    def on_closing():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()
