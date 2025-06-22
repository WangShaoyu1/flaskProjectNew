#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rasa模型训练优化脚本
专门解决"我放进去二点是青菜"类意图识别问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import yaml
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.absolute()
    rasa_root = project_root / "rasa"
    
    logger.info("🚀 开始Rasa模型优化训练...")
    logger.info(f"📁 项目根目录: {project_root}")
    logger.info(f"📁 Rasa目录: {rasa_root}")
    
    try:
        # 1. 备份原始配置
        backup_original_config(rasa_root)
        
        # 2. 整合增强训练数据
        integrate_enhanced_data(rasa_root)
        
        # 3. 使用优化配置
        use_optimized_config(rasa_root)
        
        # 4. 清理旧模型
        clean_old_models(rasa_root)
        
        # 5. 开始训练
        train_model(rasa_root)
        
        logger.info("✅ 模型优化训练完成!")
        
    except Exception as e:
        logger.error(f"❌ 训练过程中出现错误: {e}")
        sys.exit(1)

def backup_original_config(rasa_root):
    """备份原始配置"""
    logger.info("📋 备份原始配置文件...")
    
    config_file = rasa_root / "config.yml"
    nlu_file = rasa_root / "data" / "nlu.yml"
    domain_file = rasa_root / "data" / "domain.yml"
    
    if config_file.exists():
        shutil.copy2(config_file, rasa_root / "config_backup.yml")
        logger.info("✅ 已备份 config.yml")
    
    if nlu_file.exists():
        shutil.copy2(nlu_file, rasa_root / "data" / "nlu_backup.yml")
        logger.info("✅ 已备份 nlu.yml")
        
    if domain_file.exists():
        shutil.copy2(domain_file, rasa_root / "data" / "domain_backup.yml")
        logger.info("✅ 已备份 domain.yml")

def integrate_enhanced_data(rasa_root):
    """整合增强训练数据"""
    logger.info("🔄 整合增强训练数据...")
    
    enhanced_nlu_file = rasa_root / "data" / "nlu_enhanced.yml"
    original_nlu_file = rasa_root / "data" / "nlu.yml"
    
    if not enhanced_nlu_file.exists():
        logger.warning("⚠️ 增强训练数据文件不存在，跳过整合")
        return
    
    try:
        # 读取原始NLU数据
        with open(original_nlu_file, 'r', encoding='utf-8') as f:
            original_data = yaml.safe_load(f)
        
        # 读取增强NLU数据
        with open(enhanced_nlu_file, 'r', encoding='utf-8') as f:
            enhanced_data = yaml.safe_load(f)
        
        # 找到原始数据中的set_foodtype意图
        for i, intent_data in enumerate(original_data['nlu']):
            if intent_data.get('intent') == 'set_foodtype':
                # 合并训练样本
                original_examples = intent_data['examples']
                enhanced_examples = enhanced_data['nlu'][0]['examples']
                
                # 合并并去重
                combined_examples = original_examples + "\n" + enhanced_examples
                original_data['nlu'][i]['examples'] = combined_examples
                
                logger.info("✅ 已合并set_foodtype意图的训练数据")
                break
        
        # 写回原始文件
        with open(original_nlu_file, 'w', encoding='utf-8') as f:
            yaml.dump(original_data, f, default_flow_style=False, allow_unicode=True)
        
        logger.info("✅ 训练数据整合完成")
        
    except Exception as e:
        logger.error(f"❌ 整合训练数据失败: {e}")
        raise

def use_optimized_config(rasa_root):
    """使用优化配置"""
    logger.info("⚙️ 应用优化配置...")
    
    optimized_config = rasa_root / "config_optimized.yml"
    config_file = rasa_root / "config.yml"
    
    if optimized_config.exists():
        shutil.copy2(optimized_config, config_file)
        logger.info("✅ 已应用优化配置")
    else:
        logger.warning("⚠️ 优化配置文件不存在，使用原始配置")

def clean_old_models(rasa_root):
    """清理旧模型"""
    logger.info("🧹 清理旧模型...")
    
    models_dir = rasa_root / "models"
    if models_dir.exists():
        for model_file in models_dir.glob("*.tar.gz"):
            model_file.unlink()
            logger.info(f"🗑️ 已删除旧模型: {model_file.name}")
    
    logger.info("✅ 旧模型清理完成")

def train_model(rasa_root):
    """训练模型"""
    logger.info("🎯 开始训练新模型...")
    
    # 切换到rasa目录
    os.chdir(rasa_root)
    
    # 构建训练命令
    cmd = [
        "rasa", "train",
        "--config", "config.yml",
        "--domain", "data/domain.yml", 
        "--data", "data/",
        "--out", "models/",
        "--verbose"
    ]
    
    logger.info(f"🔧 执行命令: {' '.join(cmd)}")
    
    try:
        # 执行训练
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            logger.info("✅ 模型训练成功!")
            logger.info("📊 训练输出:")
            print(result.stdout)
        else:
            logger.error("❌ 模型训练失败!")
            logger.error("📊 错误输出:")
            print(result.stderr)
            raise subprocess.CalledProcessError(result.returncode, cmd)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 训练命令执行失败: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 训练过程出现异常: {e}")
        raise

if __name__ == "__main__":
    main() 