"""
H5版本后端API服务器
基于Flask，复用现有的翻译和TTS服务
"""

import os
import sys
import uuid
import time
import zipfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.translator import TranslatorService
from services.tts_service import TTSService
from config.settings import Settings


app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 初始化服务
settings = Settings()
translator = TranslatorService(settings)
tts_service = TTSService(settings)

# 全局阿里云TTS服务实例，支持动态配置
alitts_service = None

# 临时文件存储目录
TEMP_DIR = Path(__file__).parent / 'temp_files'
TEMP_DIR.mkdir(exist_ok=True)

# 任务状态存储（生产环境应使用Redis等）
task_status = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': '服务运行正常',
        'version': '1.0.0',
        'services': {
            'translator': 'available',
            'tts': 'available' if tts_service.is_available() else 'unavailable'
        }
    })


@app.route('/api/translate', methods=['POST'])
def translate_text():
    """翻译文本"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': '缺少必需参数: text'}), 400
        
        text = data['text']
        from_lang = data.get('from_lang', 'zh')
        to_lang = data.get('to_lang', 'en')
        
        if not text.strip():
            return jsonify({'error': '文本不能为空'}), 400
        
        # 调用翻译服务
        success, result = translator.translate_text(text, from_lang, to_lang)
        
        if success:
            return jsonify({
                'success': True,
                'translation': result,
                'original_text': text,
                'from_lang': from_lang,
                'to_lang': to_lang
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'翻译服务错误: {str(e)}'}), 500


@app.route('/api/synthesize', methods=['POST'])
def synthesize_voice():
    """语音合成"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': '缺少必需参数: text'}), 400
        
        text = data['text']
        voice_type = data.get('voice_type', 'girl')
        speech_rate = data.get('speech_rate', 1.0)
        source_line = data.get('source_line', '')
        
        # 对于艾彤音色，确保speech_rate是整数
        if voice_type == 'aitong':
            speech_rate = int(speech_rate)
        else:
            speech_rate = float(speech_rate)
        
        if not text.strip():
            return jsonify({'error': '文本不能为空'}), 400
        
        if not tts_service.is_available():
            return jsonify({'error': 'TTS服务不可用，请检查Google凭据配置'}), 503
        
        # 生成文件名（不包含时间戳）
        safe_source = sanitize_filename(source_line[:20] if source_line else '音频')
        safe_text = sanitize_filename(text[:20])
        
        # 如果source_line包含序号（批量生成），使用简洁的命名
        if source_line and ('_' in source_line or source_line.isdigit() or any(char.isdigit() for char in source_line[:5])):
            # 批量生成：使用source_line作为主要文件名
            filename = f"{safe_source}.wav"
        else:
            # 单个生成：使用文本内容作为文件名
            filename = f"{safe_text}.wav"
        
        # 直接使用文件名，如果存在则覆盖
        
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 保存文件路径
        output_path = TEMP_DIR / filename
        
        # 更新任务状态
        task_status[task_id] = {
            'status': 'processing',
            'progress': 0,
            'message': '正在合成语音...'
        }
        
        try:
            # 调用TTS服务 - 根据发音人类型选择不同的服务
            print(f"Synthesizing with: text='{text[:50]}...', voice_type={voice_type}, speech_rate={speech_rate}")
            
            if voice_type == 'aitong':
                # 使用阿里云TTS服务
                global alitts_service
                if alitts_service is None:
                    from services.alitts_service import AliTTSService
                    alitts_service = AliTTSService(settings)
                
                success, result = alitts_service.synthesize_speech(
                    text=text,
                    output_file=str(output_path),
                    speech_rate=speech_rate  # 已经在前端转换为阿里云格式
                )
            else:
                # 使用Google TTS服务
                success, result = tts_service.synthesize_speech(
                    text=text,
                    output_file=str(output_path),
                    voice_type=voice_type,
                    speech_rate=speech_rate
                )
            
            if success:
                # 获取文件信息
                file_size = output_path.stat().st_size
                
                task_status[task_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'message': '语音合成完成'
                }
                
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'filename': filename,
                    'audio_url': f'{request.host_url}api/audio/{filename}',
                    'download_url': f'{request.host_url}api/download/{filename}',
                    'file_size': format_file_size(file_size),
                    'duration': get_audio_duration(output_path)
                })
            else:
                task_status[task_id] = {
                    'status': 'failed',
                    'progress': 0,
                    'message': f'合成失败: {result}'
                }
                return jsonify({
                    'success': False,
                    'error': result
                }), 500
                
        except Exception as e:
            task_status[task_id] = {
                'status': 'failed',
                'progress': 0,
                'message': f'合成出错: {str(e)}'
            }
            return jsonify({
                'success': False,
                'error': f'语音合成出错: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'语音合成服务错误: {str(e)}'}), 500


@app.route('/api/preview', methods=['POST'])
def preview_voice():
    """预览语音"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': '缺少必需参数: text'}), 400
        
        text = data['text']
        voice_type = data.get('voice_type', 'girl')
        speech_rate = data.get('speech_rate', 1.0)
        
        # 对于艾彤音色，确保speech_rate是整数
        if voice_type == 'aitong':
            speech_rate = int(speech_rate)
        else:
            speech_rate = float(speech_rate)
        
        if not text.strip():
            return jsonify({'error': '文本不能为空'}), 400
        
        if not tts_service.is_available():
            return jsonify({'error': 'TTS服务不可用'}), 503
        
        # 生成预览文件名
        preview_filename = f"preview_{int(time.time())}.wav"
        preview_path = TEMP_DIR / preview_filename
        
        # 调用TTS服务 - 根据发音人类型选择不同的服务
        print(f"Preview with: text='{text[:50]}...', voice_type={voice_type}, speech_rate={speech_rate}")
        
        if voice_type == 'aitong':
            # 使用阿里云TTS服务
            global alitts_service
            if alitts_service is None:
                from services.alitts_service import AliTTSService
                alitts_service = AliTTSService(settings)
            
            success, result = alitts_service.synthesize_speech(
                text=text[:100],  # 限制预览长度
                output_file=str(preview_path),
                speech_rate=speech_rate  # 已经在前端转换为阿里云格式
            )
        else:
            # 使用Google TTS服务
            success, result = tts_service.synthesize_speech(
                text=text[:100],  # 限制预览长度
                output_file=str(preview_path),
                voice_type=voice_type,
                speech_rate=speech_rate
            )
        
        print(f"Preview TTS result: success={success}, result={result}")
        print(f"Preview file path: {preview_path}")
        print(f"Preview file exists: {preview_path.exists()}")
        
        if success:
            return jsonify({
                'success': True,
                'audio_url': f'{request.host_url}api/audio/{preview_filename}',
                'duration': get_audio_duration(preview_path)
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'预览服务错误: {str(e)}'}), 500


@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """提供音频文件"""
    try:
        file_path = TEMP_DIR / filename
        if not file_path.exists():
            abort(404)
        
        # 添加CORS头部，允许跨域访问音频文件
        response = send_file(
            file_path,
            mimetype='audio/wav',
            as_attachment=False
        )
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    except Exception as e:
        print(f"Error serving audio file {filename}: {e}")
        abort(500)


@app.route('/api/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        file_path = TEMP_DIR / filename
        if not file_path.exists():
            abort(404)
        
        return send_file(
            file_path,
            mimetype='audio/wav',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        abort(500)


@app.route('/api/batch-download', methods=['POST'])
def batch_download():
    """批量下载文件，返回ZIP压缩包"""
    try:
        data = request.get_json()
        
        if not data or 'filenames' not in data:
            return jsonify({'error': '缺少必需参数: filenames'}), 400
        
        filenames = data['filenames']
        
        if not filenames or not isinstance(filenames, list):
            return jsonify({'error': 'filenames 必须是非空数组'}), 400
        
        # 验证文件是否存在
        valid_files = []
        for filename in filenames:
            file_path = TEMP_DIR / filename
            if file_path.exists():
                valid_files.append((filename, file_path))
            else:
                print(f"Warning: File not found: {filename}")
        
        if not valid_files:
            return jsonify({'error': '没有找到有效的文件'}), 404
        
        # 生成ZIP文件名
        timestamp = int(time.time())
        zip_filename = f"voice_files_{timestamp}.zip"
        zip_path = TEMP_DIR / zip_filename
        
        # 创建ZIP文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, file_path in valid_files:
                # 生成更简洁的ZIP内文件名（去掉时间戳等）
                clean_filename = generate_clean_filename(filename)
                zipf.write(file_path, clean_filename)
        
        # 返回ZIP文件
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        print(f"Batch download error: {e}")
        return jsonify({'error': f'批量下载失败: {str(e)}'}), 500


@app.route('/api/status/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in task_status:
        return jsonify({'error': '任务不存在'}), 404
    
    return jsonify(task_status[task_id])


@app.route('/api/languages')
def get_supported_languages():
    """获取支持的语言列表"""
    languages = [
        {'code': 'zh', 'name': '中文'},
        {'code': 'en', 'name': '英文'},
        {'code': 'ja', 'name': '日文'},
        {'code': 'ko', 'name': '韩文'},
        {'code': 'auto', 'name': '自动检测'}
    ]
    
    return jsonify({'languages': languages})


@app.route('/api/voices')
def get_supported_voices():
    """获取支持的语音类型"""
    voices = [
        {'code': 'girl', 'name': '女声', 'gender': 'female'},
        {'code': 'boy', 'name': '男声', 'gender': 'male'},
        {'code': 'danbao', 'name': '蛋宝', 'gender': 'neutral'},
        {'code': 'aitong', 'name': '艾彤', 'gender': 'female'}
    ]
    
    return jsonify({'voices': voices})


@app.route('/api/aliyun/config', methods=['GET'])
def get_aliyun_config():
    """获取阿里云TTS配置"""
    try:
        global alitts_service
        if alitts_service is None:
            from services.alitts_service import AliTTSService
            alitts_service = AliTTSService(settings)
        
        token = alitts_service.get_token()
        
        return jsonify({
            'success': True,
            'token': token,
            'has_config': bool(token)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/aliyun/config', methods=['POST'])
def set_aliyun_config():
    """设置阿里云TTS配置"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '缺少配置数据'}), 400
        
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'success': False, 'error': '请输入Token'}), 400
        
        # 保存配置
        global alitts_service
        if alitts_service is None:
            from services.alitts_service import AliTTSService
            alitts_service = AliTTSService(settings)
        
        alitts_service.set_token(token)
        
        return jsonify({
            'success': True,
            'message': '配置保存成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'保存配置失败: {str(e)}'
        }), 500


@app.route('/api/aliyun/test', methods=['POST'])
def test_aliyun_connection():
    """测试阿里云TTS连接"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '缺少配置数据'}), 400
        
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'success': False, 'error': '请输入Token'}), 400
        
        # 创建临时服务实例进行测试
        global alitts_service
        if alitts_service is None:
            from services.alitts_service import AliTTSService
            alitts_service = AliTTSService(settings)
        
        # 临时设置配置
        original_token = alitts_service.get_token()
        
        alitts_service.set_token(token)
        
        try:
            # 测试连接
            success = alitts_service.test_synthesis("测试连接")
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '连接测试成功'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '连接测试失败，请检查Token是否正确'
                })
        finally:
            # 恢复原始配置
            alitts_service.set_token(original_token)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'测试连接失败: {str(e)}'
        }), 500


@app.route('/api/aliyun/url', methods=['POST'])
def generate_aliyun_url():
    """生成阿里云TTS URL（用于测试）"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        text = data.get('text', '这是一个测试').strip()
        speech_rate = data.get('speech_rate', 0)
        
        if not text:
            return jsonify({'success': False, 'error': '文本不能为空'}), 400
        
        # 创建阿里云TTS服务实例
        global alitts_service
        if alitts_service is None:
            from services.alitts_service import AliTTSService
            alitts_service = AliTTSService(settings)
        
        # 生成URL
        tts_url = alitts_service.build_tts_url(text, speech_rate)
        
        return jsonify({
            'success': True,
            'url': tts_url,
            'text': text,
            'speech_rate': speech_rate,
            'message': '阿里云TTS URL生成成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'生成URL失败: {str(e)}'
        }), 500


# 工具函数
def sanitize_filename(filename):
    """生成安全的文件名"""
    import re
    # 移除不安全字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 空格转下划线
    safe_name = re.sub(r'\s+', '_', safe_name)
    # 限制长度
    return safe_name[:50]


def generate_clean_filename(original_filename):
    """生成简洁的文件名，去掉时间戳等"""
    import re
    
    # 如果文件名已经很简洁，直接返回
    if not re.search(r'_\d{10,}', original_filename):
        return original_filename
    
    # 去掉时间戳（10位或更长的数字）
    clean_name = re.sub(r'_\d{10,}', '', original_filename)
    
    # 去掉重复的文本部分（如：1_测试_测试_123.wav -> 1_测试.wav）
    parts = clean_name.replace('.wav', '').split('_')
    if len(parts) >= 2:
        # 检查是否有重复的文本部分
        new_parts = [parts[0]]  # 保留第一部分（通常是序号）
        for i in range(1, len(parts)):
            if parts[i] not in new_parts:
                new_parts.append(parts[i])
        parts = new_parts
    
    clean_name = '_'.join(parts) + '.wav'
    
    # 确保文件名不为空
    if clean_name == '.wav':
        clean_name = 'audio.wav'
    
    return clean_name


def format_file_size(bytes_size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def get_audio_duration(file_path):
    """获取音频时长（简化版本）"""
    try:
        # 这里可以使用更精确的音频库，如 pydub
        # 暂时返回估算值
        file_size = file_path.stat().st_size
        # 粗略估算：16bit 22050Hz 单声道 WAV
        estimated_duration = file_size / (22050 * 2)
        return f"{estimated_duration:.1f}s"
    except:
        return "未知"


# 清理任务
def cleanup_old_files():
    """清理旧文件（简化版本）"""
    try:
        current_time = time.time()
        for file_path in TEMP_DIR.glob('*.wav'):
            # 删除1小时前的文件
            if current_time - file_path.stat().st_mtime > 3600:
                file_path.unlink()
    except Exception as e:
        print(f"清理文件失败: {e}")


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': '请求参数错误'}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '资源不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    import os
    
    print("=" * 60)
    print("    翻译语音生成工具 - H5版本API服务器")
    print("=" * 60)
    print(f"临时文件目录: {TEMP_DIR}")
    print(f"翻译服务状态: {'可用' if translator else '不可用'}")
    print(f"TTS服务状态: {'可用' if tts_service.is_available() else '不可用'}")
    print("\n启动服务器...")
    
    # 获取端口号（支持Heroku等平台的动态端口）
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"访问地址: http://localhost:{port}")
    print("API文档: http://localhost:{port}/api/health")
    print("\n按 Ctrl+C 停止服务器")
    
    # 定期清理旧文件
    import threading
    def periodic_cleanup():
        while True:
            time.sleep(3600)  # 每小时清理一次
            cleanup_old_files()
    
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    # 启动Flask应用
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    ) 