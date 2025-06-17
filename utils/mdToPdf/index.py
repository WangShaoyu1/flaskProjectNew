import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from pathlib import Path
from typing import Dict, Optional
import threading
import re
from PIL import Image, ImageTk
import io

import os
import tempfile
import shutil
import subprocess
import logging


def convert_md_to_pdf(input_md, output_pdf=None, **kwargs):
    """
    将Markdown文件转换为PDF（增强稳定性版本）

    参数:
        input_md: 输入的Markdown文件路径
        output_pdf: 输出的PDF文件路径（可选）
        **kwargs: 其他Pandoc参数

    返回:
        转换成功返回True，失败返回False
    """
    # 设置日志记录
    logging.basicConfig(filename='md2pdf.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # 1. 路径处理（解决中文路径问题）
    try:
        # 创建临时工作目录（纯ASCII路径）
        with tempfile.TemporaryDirectory(prefix="md2pdf_") as tmp_dir:
            tmp_md = os.path.join(tmp_dir, "source.md")

            # 复制源文件到临时目录
            shutil.copy2(input_md, tmp_md)
            logging.info(f"Copied source to temporary location: {tmp_md}")

            # 2. 构建基础命令
            cmd = [
                'pandoc',
                tmp_md,
                '-o', output_pdf or os.path.splitext(input_md)[0] + '.pdf',
                '--pdf-engine=xelatex',
                '-V', f'CJKmainfont={kwargs.get("CJKmainfont", "Microsoft YaHei")}',
                '-V', f'CJKmonofont={kwargs.get("CJKmonofont", "Microsoft YaHei")}',
                '-V', f'monofont={kwargs.get("monofont", "Consolas")}',
                '--highlight-style', kwargs.get('highlight_style', 'breezedark'),
                '--toc',
                '-N',
                '--wrap=auto'
            ]

            # 3. 安全构建header-includes（关键修复）
            latex_packages = [
                r'\usepackage{fvextra}',
                r'\usepackage[top=1.7cm,bottom=1.7cm,left=1.7cm,right=1.7cm]{geometry}',
                r'\definecolor{shadecolor}{RGB}{245,245,245}',
                r'\DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaksymbolleft={},commandchars=\\\{\}}'
            ]

            # 添加自定义header（如果有）
            if 'header_includes' in kwargs:
                latex_packages.append(kwargs['header_includes'])

            # 安全拼接参数（使用双引号包裹）
            header_str = ''.join(latex_packages)
            cmd.extend(['-V', f'header-includes={header_str}'])

            # 4. 执行转换
            logging.info(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 5. 错误处理
            if result.returncode != 0:
                error_msg = f"Pandoc转换失败(代码{result.returncode}):\n{result.stderr}"
                logging.error(error_msg)

                # 检查特定字体错误
                if "miktex-makemf" in result.stderr or "Microso.cfg" in result.stderr:
                    logging.warning("检测到MiKTeX字体生成错误，尝试修复...")
                    fix_font_issues()
                    # 重试一次
                    return convert_md_to_pdf(input_md, output_pdf, **kwargs)

                raise RuntimeError(error_msg)

            logging.info("PDF转换成功完成")
            return True

    except Exception as e:
        logging.exception("转换过程中发生未预期错误")
        raise


def fix_font_issues():
    """尝试自动修复字体相关问题"""
    try:
        # 更新MiKTeX包数据库
        subprocess.run(
            ["mpm", "--admin", "--update-db"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # 强制重建字体缓存
        subprocess.run(
            ["initexmf", "--admin", "--force", "--mklinks"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logging.info("MiKTeX字体缓存已成功重建")
    except subprocess.CalledProcessError as e:
        logging.error(f"字体修复失败: {e}")
        raise RuntimeError("自动修复字体失败，请手动执行管理员命令") from e


class ModernPDFConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MD转PDF工具")
        self.root.geometry("800x650")
        self.root.resizable(True, True)

        # 现代互联网风格颜色
        self.PRIMARY_COLOR = "#4285F4"  # Google Blue
        self.SECONDARY_COLOR = "#34A853"  # Google Green
        self.BACKGROUND_COLOR = "#F8F9FA"  # Light background
        self.CARD_COLOR = "#FFFFFF"  # Card background
        self.TEXT_COLOR = "#202124"  # Primary text
        self.SUBTEXT_COLOR = "#5F6368"  # Secondary text

        # 配置现代UI样式
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 自定义样式
        self.style.configure('TFrame', background=self.BACKGROUND_COLOR)
        self.style.configure('TLabel', background=self.CARD_COLOR, foreground=self.TEXT_COLOR)
        self.style.configure('TLabelframe', background=self.CARD_COLOR, borderwidth=2, relief="flat")
        self.style.configure('TLabelframe.Label', background=self.CARD_COLOR, foreground=self.TEXT_COLOR)
        self.style.configure('TButton', background="#E8EAED", borderwidth=1, relief="flat")
        self.style.map('TButton',
                       background=[('active', '#DADCE0')],
                       relief=[('pressed', 'sunken')])

        # 主框架
        self.main_frame = ttk.Frame(root, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 主标题
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            title_frame,
            text="MD转PDF工具",
            font=('微软雅黑', 16, 'bold'),
            foreground=self.PRIMARY_COLOR,
            anchor="center"
        )
        title_label.pack(fill=tk.X)

        # 副标题
        subtitle_label = ttk.Label(
            title_frame,
            text="将Markdown文件转换为精美的PDF文档",
            font=('微软雅黑', 10),
            foreground=self.SUBTEXT_COLOR,
            anchor="center"
        )
        subtitle_label.pack(fill=tk.X, pady=(0, 0))

        # 内容区域
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # ====== 左侧区域 ======
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # 文件选择卡片
        file_card = ttk.LabelFrame(left_frame, text="📁 文件选择")
        file_card.pack(fill=tk.BOTH, expand=True)

        # 文件列表容器（添加了滚动条支持的容器）
        self.list_container = ttk.Frame(file_card)
        self.list_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加X轴和Y轴滚动条
        self.scroll_y = ttk.Scrollbar(self.list_container, orient="vertical")
        self.scroll_x = ttk.Scrollbar(self.list_container, orient="horizontal")

        # 创建文件列表框（支持水平和垂直滚动）
        self.file_listbox = tk.Listbox(
            self.list_container,
            height=10,
            width=40,
            selectmode=tk.EXTENDED,
            bd=0,
            bg="#FFFFFF",
            highlightthickness=0,
            font=('微软雅黑', 10),
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )

        # 配置滚动条回调
        self.scroll_y.config(command=self.file_listbox.yview)
        self.scroll_x.config(command=self.file_listbox.xview)

        # 使用grid布局管理滚动条位置
        self.file_listbox.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        # 配置网格行列权重（使列表框可扩展）
        self.list_container.columnconfigure(0, weight=1)
        self.list_container.rowconfigure(0, weight=1)

        # 按钮区域
        button_frame = ttk.Frame(file_card)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.clear_btn = ttk.Button(
            button_frame,
            text="清除全部",
            command=self.clear_files
        )
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.add_btn = ttk.Button(
            button_frame,
            text="添加文件",
            command=self.add_files,
            style="Accent.TButton"
        )
        self.add_btn.pack(side=tk.RIGHT)

        # ====== 底部转换控制区 ======
        control_card = ttk.Frame(left_frame)
        control_card.pack(fill=tk.X, pady=(15, 0))

        # 进度条
        self.progress = ttk.Progressbar(
            control_card,
            orient=tk.HORIZONTAL,
            mode='determinate',
            length=0
        )
        self.progress.pack(fill=tk.X, padx=10, pady=10)

        # 开始转换按钮
        self.convert_btn = ttk.Button(
            control_card,
            text="开始转换",
            command=self.start_conversion,
            style="Primary.TButton"
        )
        self.convert_btn.pack(fill=tk.X, padx=10, pady=(0, 10))

        # ====== 右侧参数设置区域 ======
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 参数设置卡片
        param_card = ttk.LabelFrame(right_frame, text="⚙️ 转换设置")
        param_card.pack(fill=tk.BOTH, expand=True)

        # 边距设置
        margin_label = ttk.Label(
            param_card,
            text="页面边距设置",
            font=('微软雅黑', 10, 'bold'),
            foreground=self.PRIMARY_COLOR
        )
        margin_label.pack(anchor=tk.W, padx=10, pady=(10, 5))

        margins = [('上边距:', 'top_margin'), ('下边距:', 'bottom_margin'),
                   ('左边距:', 'left_margin'), ('右边距:', 'right_margin')]

        for label, name in margins:
            item_frame = ttk.Frame(param_card)
            item_frame.pack(fill=tk.X, padx=15, pady=7)

            ttk.Label(item_frame, text=label, width=8, anchor="e").pack(side=tk.LEFT, padx=(0, 10))

            entry = ttk.Entry(item_frame, width=10)
            entry.insert(0, "1.7cm")
            entry.pack(side=tk.LEFT)
            setattr(self, name, entry)

        # 分隔线
        separator = ttk.Separator(param_card, orient="horizontal")
        separator.pack(fill=tk.X, padx=10, pady=10)

        # 代码块设置
        code_label = ttk.Label(
            param_card,
            text="代码块样式",
            font=('微软雅黑', 10, 'bold'),
            foreground=self.PRIMARY_COLOR
        )
        code_label.pack(anchor=tk.W, padx=10, pady=(0, 5))

        # 启用颜色选项
        self.enable_color_var = tk.BooleanVar(value=True)
        self.enable_color_check = ttk.Checkbutton(
            param_card,
            text="启用代码块背景色",
            variable=self.enable_color_var,
            command=self.toggle_color_preview
        )
        self.enable_color_check.pack(anchor=tk.W, padx=15, pady=(0, 10))

        # 颜色输入区域
        color_frame = ttk.Frame(param_card)
        color_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        # 颜色表示选项
        self.color_mode = tk.StringVar(value="hex")
        hex_radio = ttk.Radiobutton(
            color_frame,
            text="HEX",
            variable=self.color_mode,
            value="hex",
            command=self.update_color_input
        )
        hex_radio.grid(row=0, column=0, padx=(0, 10))

        rgb_radio = ttk.Radiobutton(
            color_frame,
            text="RGB",
            variable=self.color_mode,
            value="rgb",
            command=self.update_color_input
        )
        rgb_radio.grid(row=0, column=1, padx=(0, 10))

        rgba_radio = ttk.Radiobutton(
            color_frame,
            text="RGBA",
            variable=self.color_mode,
            value="rgba",
            command=self.update_color_input
        )
        rgba_radio.grid(row=0, column=2)

        # 颜色输入框
        color_input_frame = ttk.Frame(param_card)
        color_input_frame.pack(fill=tk.X, padx=15, pady=(5, 10))

        self.color_value = tk.StringVar()
        self.color_value.set("#f5f5f5")
        self.color_entry = ttk.Entry(
            color_input_frame,
            textvariable=self.color_value,
            font=('Consolas', 10)
        )
        self.color_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # 颜色预览
        self.color_preview = tk.Canvas(
            color_input_frame,
            width=30,
            height=30,
            bg="#f5f5f5",
            bd=1,
            relief="flat",
            highlightthickness=0
        )
        self.color_preview.pack(side=tk.LEFT, padx=(0, 10))

        # 专业颜色选择器按钮
        self.color_picker_btn = ttk.Button(
            color_input_frame,
            text="选择颜色",
            command=self.open_color_picker,
            style="Accent.TButton"
        )
        self.color_picker_btn.pack(side=tk.RIGHT)

        # 文件计数器
        self.file_counter = ttk.Label(
            left_frame,
            text="已选择 0 个文件",
            font=('微软雅黑', 9),
            foreground=self.SUBTEXT_COLOR
        )
        self.file_counter.pack(side=tk.TOP, anchor="w", pady=(5, 0))

        # 配置专业按钮样式
        self.style.configure('Primary.TButton',
                             foreground='white',
                             background=self.PRIMARY_COLOR,
                             font=('微软雅黑', 10, 'bold'),
                             borderwidth=0,
                             padding=8)
        self.style.map('Primary.TButton',
                       background=[('active', '#3367D6'), ('pressed', '#2B5ABF')])

        self.style.configure('Accent.TButton',
                             background=self.SECONDARY_COLOR,
                             foreground='white',
                             font=('微软雅黑', 9))
        self.style.map('Accent.TButton',
                       background=[('active', '#2D9147'), ('pressed', '#248038')])

        # 绑定事件
        self.file_listbox.bind('<<ListboxSelect>>', self.update_file_counter)
        self.color_entry.bind("<KeyRelease>", self.update_color_preview)

    def add_files(self):
        """添加多个MD文件"""
        files = filedialog.askopenfilenames(
            title="选择Markdown文件",
            filetypes=[("Markdown文件", "*.md"), ("所有文件", "*.*")]
        )

        for file in files:
            if file and file not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, file)

        self.update_file_counter()

    def clear_files(self):
        """清除所有文件"""
        self.file_listbox.delete(0, tk.END)
        self.update_file_counter()

    def update_file_counter(self, event=None):
        """更新文件计数"""
        count = self.file_listbox.size()
        self.file_counter.config(text=f"已选择 {count} 个文件")

    def toggle_color_preview(self):
        """启用/禁用颜色预览"""
        state = tk.NORMAL if self.enable_color_var.get() else tk.DISABLED
        self.color_entry.config(state=state)
        self.color_preview.config(state=state)
        self.color_picker_btn.config(state=state)

    def update_color_preview(self, event=None):
        """更新颜色预览"""
        if not self.enable_color_var.get():
            return

        color_val = self.color_value.get()
        try:
            self.color_preview.config(bg=color_val)
        except tk.TclError:
            pass

    def update_color_input(self):
        """根据选择的颜色模式更新输入框"""
        current_color = self.color_entry.get()

        try:
            if self.color_mode.get() == "hex" and not current_color.startswith("#"):
                if current_color.startswith("rgb") or current_color.startswith("rgba"):
                    r, g, b, *a = re.findall(r'\d+', current_color)
                    hex_value = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
                    self.color_value.set(hex_value)

            elif self.color_mode.get() == "rgb" and not current_color.startswith("rgb("):
                if current_color.startswith("#"):
                    r = int(current_color[1:3], 16)
                    g = int(current_color[3:5], 16)
                    b = int(current_color[5:7], 16)
                    self.color_value.set(f"rgb({r}, {g}, {b})")
                elif current_color.startswith("rgba("):
                    r, g, b, a = re.findall(r'[\d.]+', current_color)
                    self.color_value.set(f"rgb({r}, {g}, {b})")

            elif self.color_mode.get() == "rgba" and not current_color.startswith("rgba("):
                alpha = 1.0
                if current_color.startswith("#"):
                    r = int(current_color[1:3], 16)
                    g = int(current_color[3:5], 16)
                    b = int(current_color[5:7], 16)
                elif current_color.startswith("rgb("):
                    r, g, b = re.findall(r'\d+', current_color)
                self.color_value.set(f"rgba({r}, {g}, {b}, {alpha})")

            self.update_color_preview()
        except Exception as e:
            print(f"颜色转换错误: {str(e)}")

    def open_color_picker(self):
        """打开专业颜色选择器"""
        # 尝试解析当前颜色
        current_color = self.color_value.get()
        initial_color = "#4285F4"  # 默认Google蓝色

        if current_color:
            try:
                if current_color.startswith("#"):
                    initial_color = current_color
                elif current_color.startswith("rgb("):
                    r, g, b = re.findall(r'\d+', current_color)
                    initial_color = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
                elif current_color.startswith("rgba("):
                    r, g, b, a = re.findall(r'[\d.]+', current_color)
                    initial_color = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
            except:
                pass

        # 打开系统颜色选择器
        color = colorchooser.askcolor(
            title="选择代码块背景色",
            initialcolor=initial_color
        )

        if color[1]:  # 用户选择了颜色
            hex_value = color[1]

            if self.color_mode.get() == "hex":
                self.color_value.set(hex_value)
            elif self.color_mode.get() == "rgb":
                r = int(hex_value[1:3], 16)
                g = int(hex_value[3:5], 16)
                b = int(hex_value[5:7], 16)
                self.color_value.set(f"rgb({r}, {g}, {b})")
            elif self.color_mode.get() == "rgba":
                r = int(hex_value[1:3], 16)
                g = int(hex_value[3:5], 16)
                b = int(hex_value[5:7], 16)
                self.color_value.set(f"rgba({r}, {g}, {b}, 1.0)")

            self.update_color_preview()

    def get_conversion_params(self):
        """获取转换参数"""
        return {
            'margins': {
                'top': self.top_margin.get(),
                'bottom': self.bottom_margin.get(),
                'left': self.left_margin.get(),
                'right': self.right_margin.get()
            },
            'code_bg_color': self.color_value.get() if self.enable_color_var.get() else None
        }

    def start_conversion(self):
        """开始转换文件"""
        selected_files = self.file_listbox.get(0, tk.END)
        if not selected_files:
            messagebox.showwarning("提示", "请至少选择一个Markdown文件")
            return

        # 禁用按钮防止重复点击
        self.convert_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.progress['maximum'] = len(selected_files)

        # 启动转换线程
        threading.Thread(
            target=self.convert_files,
            args=(selected_files,),
            daemon=True
        ).start()

    def convert_files(self, files):
        """转换文件批处理"""
        params = self.get_conversion_params()
        total_files = len(files)
        self.progress['maximum'] = total_files
        success_count = 0
        errors = []

        for i, file in enumerate(files, 1):
            try:
                convert_md_to_pdf(file, **params)
                success_count += 1
            except Exception as e:
                filename = os.path.basename(file)
                errors.append(f"{filename}: {str(e)}")

            # 修复后的进度更新代码
            self.root.after(0, lambda val=i: self.progress.config(value=val))

        # 完成处理
        self.root.after(0, self.on_conversion_complete, total_files, success_count, errors)

    def on_conversion_complete(self, total_files, success_count, errors):
        """转换完成处理"""
        self.convert_btn.config(state=tk.NORMAL)

        # 创建自定义消息框窗口
        msg_window = tk.Toplevel(self.root)
        msg_window.title("转换结果")
        msg_window.geometry("900x600")  # 固定宽高
        msg_window.resizable(False, False)  # 禁止调整大小
        msg_window.transient(self.root)  # 设为子窗口
        msg_window.grab_set()  # 模态窗口

        # 主框架
        main_frame = ttk.Frame(msg_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建带滚动条的文本框
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(text_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 创建文本框
        text_box = tk.Text(
            text_frame,
            wrap=tk.NONE,  # 不自动换行
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            font=('微软雅黑', 10),
            padx=10,
            pady=10
        )
        text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置滚动条
        scroll_y.config(command=text_box.yview)
        scroll_x.config(command=text_box.xview)

        # 添加内容
        if errors:
            header = f"✅ 成功: {success_count}个文件\n❌ 失败: {len(errors)}个文件\n\n错误详情:\n"
            text_box.insert(tk.END, header)
            text_box.tag_add("header", "1.0", "3.0")
            text_box.tag_config("header", font=('微软雅黑', 10, 'bold'))

            for i, error in enumerate(errors[:10]):  # 最多显示10个错误
                text_box.insert(tk.END, f"{i + 1}. {error}\n")
        else:
            success_msg = f"✅ 所有文件转换成功!\n总共转换了 {total_files} 个文件"
            text_box.insert(tk.END, success_msg)
            text_box.tag_add("success", "1.0", "end")
            text_box.tag_config("success", foreground="green", font=('微软雅黑', 10, 'bold'))

        # 设为只读
        text_box.config(state=tk.DISABLED)

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        # 复制按钮
        copy_btn = ttk.Button(
            btn_frame,
            text="复制内容",
            command=lambda: self.copy_to_clipboard(text_box),
            width=10
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 确定按钮
        ok_btn = ttk.Button(
            btn_frame,
            text="确定",
            command=msg_window.destroy,
            width=10,
            style='Accent.TButton'
        )
        ok_btn.pack(side=tk.RIGHT)

    def copy_to_clipboard(self, text_widget):
        """将文本框内容复制到剪贴板"""
        # 临时启用文本框以获取内容
        text_widget.config(state=tk.NORMAL)
        content = text_widget.get("1.0", tk.END)
        text_widget.config(state=tk.DISABLED)

        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(content.strip())

        # 显示复制成功提示
        tk.messagebox.showinfo("复制成功", "内容已复制到剪贴板！", parent=text_widget.winfo_toplevel())


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernPDFConverterApp(root)
    root.mainloop()
