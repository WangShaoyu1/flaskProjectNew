"""
指令库版本管理器
管理Excel解析后的YML文件与指令库版本的关联
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LibraryVersionManager:
    """指令库版本管理器"""
    
    def __init__(self, rasa_root: str = "rasa"):
        # 获取项目根目录
        current_dir = Path(__file__).parent.parent.parent
        self.rasa_root = current_dir / rasa_root
        self.data_dir = self.rasa_root / "data"
        self.versions_dir = self.rasa_root / "versions"
        self.library_versions_dir = self.rasa_root / "library_versions"
        
        # 确保目录存在
        self.library_versions_dir.mkdir(exist_ok=True)
        self.versions_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        self.config_files = [
            'config.yml',
            'domain.yml',
            'nlu.yml',
            'rules.yml',
            'stories.yml'
        ]
    
    def create_library_version(self, library_id: int, library_name: str, 
                             version_name: Optional[str] = None, 
                             description: str = "") -> str:
        """
        为指令库创建新版本
        
        Args:
            library_id: 指令库ID
            library_name: 指令库名称
            version_name: 版本名称（可选，默认自动生成）
            description: 版本描述
            
        Returns:
            str: 版本目录名称
        """
        try:
            # 生成版本名称
            if not version_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                version_name = f"v{timestamp}"
            
            # 创建版本目录
            library_dir = self.library_versions_dir / f"library_{library_id}"
            version_dir = library_dir / version_name
            
            library_dir.mkdir(exist_ok=True)
            version_dir.mkdir(exist_ok=True)
            
            # 复制当前工作区文件到版本目录
            self._copy_current_files_to_version(version_dir)
            
            # 创建版本信息文件
            version_info = {
                'library_id': library_id,
                'library_name': library_name,
                'version_name': version_name,
                'description': description,
                'created_time': datetime.now().isoformat(),
                'file_paths': {
                    'config.yml': str(version_dir / 'config.yml'),
                    'domain.yml': str(version_dir / 'domain.yml'),
                    'nlu.yml': str(version_dir / 'nlu.yml'),
                    'rules.yml': str(version_dir / 'rules.yml'),
                    'stories.yml': str(version_dir / 'stories.yml')
                }
            }
            
            # 保存版本信息
            version_info_path = version_dir / 'version_info.json'
            with open(version_info_path, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, ensure_ascii=False, indent=2)
            
            # 更新指令库版本索引
            self._update_library_index(library_id, library_name, version_name, version_info)
            
            logger.info(f"为指令库 {library_id} 创建版本 {version_name}")
            return version_name
            
        except Exception as e:
            logger.error(f"创建指令库版本失败: {str(e)}")
            raise Exception(f"版本创建错误: {str(e)}")
    
    def save_excel_generated_files(self, library_id: int, library_name: str,
                                 file_contents: Dict[str, str],
                                 version_name: Optional[str] = None,
                                 description: str = "Excel导入生成") -> str:
        """
        保存Excel解析生成的YML文件
        
        Args:
            library_id: 指令库ID
            library_name: 指令库名称
            file_contents: 文件内容字典 {'filename': 'content'}
            version_name: 版本名称（可选）
            description: 版本描述
            
        Returns:
            str: 版本目录名称
        """
        try:
            # 生成版本名称
            if not version_name:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                version_name = f"v{timestamp}_excel_import"
            
            # 创建版本目录
            library_dir = self.library_versions_dir / f"library_{library_id}"
            version_dir = library_dir / version_name
            
            library_dir.mkdir(exist_ok=True)
            version_dir.mkdir(exist_ok=True)
            
            # 保存文件内容
            saved_files = {}
            for filename, content in file_contents.items():
                if filename.endswith('.yml') or filename.endswith('.yaml'):
                    file_path = version_dir / filename
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    saved_files[filename] = str(file_path)
                    logger.info(f"保存文件: {file_path}")
            
            # 复制config.yml（如果没有提供）
            if 'config.yml' not in file_contents:
                config_source = self.rasa_root / 'config.yml'
                if config_source.exists():
                    config_dest = version_dir / 'config.yml'
                    shutil.copy2(config_source, config_dest)
                    saved_files['config.yml'] = str(config_dest)
            
            # 创建版本信息文件
            version_info = {
                'library_id': library_id,
                'library_name': library_name,
                'version_name': version_name,
                'description': description,
                'created_time': datetime.now().isoformat(),
                'source': 'excel_import',
                'file_paths': saved_files,
                'statistics': self._analyze_files(file_contents)
            }
            
            # 保存版本信息
            version_info_path = version_dir / 'version_info.json'
            with open(version_info_path, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, ensure_ascii=False, indent=2)
            
            # 更新指令库版本索引
            self._update_library_index(library_id, library_name, version_name, version_info)
            
            # 同步到工作区（可选）
            self._sync_to_workspace(version_dir)
            
            logger.info(f"Excel生成文件已保存到指令库 {library_id} 版本 {version_name}")
            return version_name
            
        except Exception as e:
            logger.error(f"保存Excel生成文件失败: {str(e)}")
            raise Exception(f"文件保存错误: {str(e)}")
    
    def get_library_versions(self, library_id: int) -> List[Dict[str, Any]]:
        """
        获取指令库的所有版本
        
        Args:
            library_id: 指令库ID
            
        Returns:
            List[Dict]: 版本信息列表
        """
        try:
            library_dir = self.library_versions_dir / f"library_{library_id}"
            if not library_dir.exists():
                return []
            
            versions = []
            for version_dir in library_dir.iterdir():
                if version_dir.is_dir():
                    version_info_path = version_dir / 'version_info.json'
                    if version_info_path.exists():
                        with open(version_info_path, 'r', encoding='utf-8') as f:
                            version_info = json.load(f)
                        versions.append(version_info)
            
            # 按创建时间排序
            versions.sort(key=lambda x: x['created_time'], reverse=True)
            return versions
            
        except Exception as e:
            logger.error(f"获取指令库版本失败: {str(e)}")
            return []
    
    def get_version_files(self, library_id: int, version_name: str) -> Dict[str, str]:
        """
        获取指定版本的文件内容
        
        Args:
            library_id: 指令库ID
            version_name: 版本名称
            
        Returns:
            Dict[str, str]: 文件内容字典
        """
        try:
            version_dir = self.library_versions_dir / f"library_{library_id}" / version_name
            if not version_dir.exists():
                return {}
            
            files_content = {}
            for config_file in self.config_files:
                file_path = version_dir / config_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[config_file] = f.read()
            
            return files_content
            
        except Exception as e:
            logger.error(f"获取版本文件失败: {str(e)}")
            return {}
    
    def activate_version(self, library_id: int, version_name: str) -> bool:
        """
        激活指定版本到工作区
        
        Args:
            library_id: 指令库ID
            version_name: 版本名称
            
        Returns:
            bool: 是否成功
        """
        try:
            version_dir = self.library_versions_dir / f"library_{library_id}" / version_name
            if not version_dir.exists():
                logger.error(f"版本目录不存在: {version_dir}")
                return False
            
            # 备份当前工作区
            backup_dir = self.data_dir.parent / f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if self.data_dir.exists():
                shutil.copytree(self.data_dir, backup_dir)
                logger.info(f"当前工作区已备份到: {backup_dir}")
            
            # 复制版本文件到工作区
            self.data_dir.mkdir(exist_ok=True)
            
            for config_file in self.config_files:
                source_file = version_dir / config_file
                if source_file.exists():
                    if config_file == 'config.yml':
                        dest_file = self.rasa_root / config_file
                    else:
                        dest_file = self.data_dir / config_file
                    
                    shutil.copy2(source_file, dest_file)
                    logger.info(f"激活文件: {config_file}")
            
            # 更新激活状态
            self._update_active_version(library_id, version_name)
            
            logger.info(f"版本 {version_name} 已激活到工作区")
            return True
            
        except Exception as e:
            logger.error(f"激活版本失败: {str(e)}")
            return False
    
    def delete_version(self, library_id: int, version_name: str) -> bool:
        """
        删除指定版本
        
        Args:
            library_id: 指令库ID
            version_name: 版本名称
            
        Returns:
            bool: 是否成功
        """
        try:
            version_dir = self.library_versions_dir / f"library_{library_id}" / version_name
            if version_dir.exists():
                shutil.rmtree(version_dir)
                logger.info(f"版本 {version_name} 已删除")
                
                # 更新索引
                self._remove_from_library_index(library_id, version_name)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除版本失败: {str(e)}")
            return False
    
    def _copy_current_files_to_version(self, version_dir: Path):
        """复制当前工作区文件到版本目录"""
        for config_file in self.config_files:
            if config_file == 'config.yml':
                source_file = self.rasa_root / config_file
            else:
                source_file = self.data_dir / config_file
            
            if source_file.exists():
                dest_file = version_dir / config_file
                shutil.copy2(source_file, dest_file)
    
    def _sync_to_workspace(self, version_dir: Path):
        """同步版本文件到工作区"""
        self.data_dir.mkdir(exist_ok=True)
        
        for config_file in self.config_files:
            source_file = version_dir / config_file
            if source_file.exists():
                if config_file == 'config.yml':
                    dest_file = self.rasa_root / config_file
                else:
                    dest_file = self.data_dir / config_file
                
                shutil.copy2(source_file, dest_file)
    
    def _update_library_index(self, library_id: int, library_name: str, 
                            version_name: str, version_info: Dict[str, Any]):
        """更新指令库版本索引"""
        index_file = self.library_versions_dir / 'library_index.json'
        
        # 读取现有索引
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {}
        
        # 更新索引
        library_key = str(library_id)
        if library_key not in index:
            index[library_key] = {
                'library_id': library_id,
                'library_name': library_name,
                'versions': [],
                'active_version': None
            }
        
        # 添加版本信息
        version_summary = {
            'version_name': version_name,
            'description': version_info['description'],
            'created_time': version_info['created_time'],
            'source': version_info.get('source', 'manual')
        }
        
        # 检查版本是否已存在
        existing_versions = [v['version_name'] for v in index[library_key]['versions']]
        if version_name not in existing_versions:
            index[library_key]['versions'].append(version_summary)
        
        # 保存索引
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _remove_from_library_index(self, library_id: int, version_name: str):
        """从索引中移除版本"""
        index_file = self.library_versions_dir / 'library_index.json'
        if not index_file.exists():
            return
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        library_key = str(library_id)
        if library_key in index:
            index[library_key]['versions'] = [
                v for v in index[library_key]['versions'] 
                if v['version_name'] != version_name
            ]
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _update_active_version(self, library_id: int, version_name: str):
        """更新激活版本"""
        index_file = self.library_versions_dir / 'library_index.json'
        if not index_file.exists():
            return
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        library_key = str(library_id)
        if library_key in index:
            index[library_key]['active_version'] = version_name
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _analyze_files(self, file_contents: Dict[str, str]) -> Dict[str, Any]:
        """分析文件内容统计信息"""
        stats = {
            'total_files': len(file_contents),
            'file_sizes': {},
            'has_nlu': 'nlu.yml' in file_contents,
            'has_domain': 'domain.yml' in file_contents,
            'has_rules': 'rules.yml' in file_contents,
            'has_stories': 'stories.yml' in file_contents
        }
        
        for filename, content in file_contents.items():
            stats['file_sizes'][filename] = len(content.encode('utf-8'))
        
        return stats
    
    def get_library_index(self) -> Dict[str, Any]:
        """获取所有指令库的版本索引"""
        index_file = self.library_versions_dir / 'library_index.json'
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {} 