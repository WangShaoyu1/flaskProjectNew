"""
文件管理服务
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple
from config.settings import Settings


class FileManager:
    """文件管理器"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_save_path(self) -> str:
        """获取保存路径"""
        return self.settings.get('last_save_path', str(Path.home() / 'Downloads'))
    
    def set_save_path(self, path: str):
        """设置保存路径"""
        if os.path.isdir(path):
            self.settings.set('last_save_path', path)
            return True
        return False
    
    def generate_filename(self, prefix: str = 'audio', index: Optional[int] = None, extension: str = 'wav') -> str:
        """
        生成文件名
        
        Args:
            prefix: 文件名前缀
            index: 文件索引（用于批量文件）
            extension: 文件扩展名
            
        Returns:
            生成的文件名
        """
        timestamp = int(time.time())
        
        if index is not None:
            return f"{prefix}_{index:03d}_{timestamp}.{extension}"
        else:
            return f"{prefix}_{timestamp}.{extension}"
    
    def get_output_path(self, filename: str, custom_dir: Optional[str] = None) -> str:
        """
        获取输出文件的完整路径
        
        Args:
            filename: 文件名
            custom_dir: 自定义目录（可选）
            
        Returns:
            完整的文件路径
        """
        if custom_dir:
            output_dir = custom_dir
        else:
            output_dir = self.get_save_path()
        
        return str(Path(output_dir) / filename)
    
    def ensure_directory(self, path: str) -> bool:
        """
        确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            是否成功创建或目录已存在
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"创建目录失败: {e}")
            return False
    
    def is_valid_path(self, path: str) -> bool:
        """
        检查路径是否有效
        
        Args:
            path: 要检查的路径
            
        Returns:
            路径是否有效
        """
        try:
            path_obj = Path(path)
            # 检查父目录是否存在或可以创建
            if path_obj.parent.exists():
                return True
            else:
                # 尝试创建父目录
                return self.ensure_directory(str(path_obj.parent))
        except Exception:
            return False
    
    def get_file_size(self, filepath: str) -> Optional[int]:
        """
        获取文件大小
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件大小（字节），如果文件不存在返回None
        """
        try:
            return Path(filepath).stat().st_size
        except Exception:
            return None
    
    def delete_file(self, filepath: str) -> bool:
        """
        删除文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否成功删除
        """
        try:
            Path(filepath).unlink()
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    def list_audio_files(self, directory: str) -> list:
        """
        列出目录中的音频文件
        
        Args:
            directory: 目录路径
            
        Returns:
            音频文件列表
        """
        audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg'}
        audio_files = []
        
        try:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                for file_path in dir_path.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                        audio_files.append(str(file_path))
        except Exception as e:
            print(f"列出音频文件失败: {e}")
        
        return sorted(audio_files)
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        格式化文件大小显示
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化后的文件大小字符串
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB" 