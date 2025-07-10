import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 
           (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000'),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API请求:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API响应:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('API响应错误:', error.response?.status, error.response?.data || error.message);
    
    if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请检查网络连接';
    } else if (error.response?.status === 404) {
      error.message = 'API接口不存在，请检查服务器配置';
    } else if (error.response?.status === 500) {
      error.message = '服务器内部错误，请联系管理员';
    } else if (error.message === 'Network Error') {
      error.message = '无法连接到服务器，请检查API地址设置';
    }
    
    return Promise.reject(error);
  }
);

// API服务类
class APIService {
  // 健康检查
  async healthCheck() {
    try {
      const response = await api.get('/api/health');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 翻译文本
  async translateText(text, fromLang = 'zh', toLang = 'en') {
    try {
      const response = await api.post('/api/translate', {
        text,
        from_lang: fromLang,
        to_lang: toLang
      });
      
      return {
        success: true,
        translation: response.data.translation,
        originalText: text
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        originalText: text
      };
    }
  }

  // 语音合成
  async synthesizeVoice(text, options = {}) {
    try {
      const {
        voiceType = 'girl',
        speechRate = 1.0,
        sourceLine = ''
      } = options;

      const response = await api.post('/api/synthesize', {
        text,
        voice_type: voiceType,
        speech_rate: speechRate,
        source_line: sourceLine
      });

      return {
        success: true,
        file: {
          name: response.data.filename,
          url: response.data.audio_url,
          downloadUrl: response.data.download_url,
          size: response.data.file_size || '未知',
          duration: response.data.duration || '未知'
        },
        taskId: response.data.task_id
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 预览语音
  async previewVoice(text, options = {}) {
    try {
      const {
        voiceType = 'girl',
        speechRate = 1.0
      } = options;

      const response = await api.post('/api/preview', {
        text,
        voice_type: voiceType,
        speech_rate: speechRate
      });

      return {
        success: true,
        audioUrl: response.data.audio_url,
        duration: response.data.duration
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 获取支持的语言列表
  async getSupportedLanguages() {
    try {
      const response = await api.get('/api/languages');
      return {
        success: true,
        languages: response.data.languages
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        languages: this.getDefaultLanguages()
      };
    }
  }

  // 获取支持的语音类型
  async getSupportedVoices() {
    try {
      const response = await api.get('/api/voices');
      return {
        success: true,
        voices: response.data.voices
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        voices: this.getDefaultVoices()
      };
    }
  }

  // 获取阿里云配置
  async getAliyunConfig() {
    try {
      const response = await api.get('/api/aliyun/config');
      return {
        success: true,
        ...response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 设置阿里云配置
  async setAliyunConfig(token) {
    try {
      const response = await api.post('/api/aliyun/config', {
        token
      });
      return {
        success: true,
        ...response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 测试阿里云连接
  async testAliyunConnection(token) {
    try {
      const response = await api.post('/api/aliyun/test', {
        token
      });
      return {
        success: true,
        ...response.data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 批量下载ZIP文件
  async batchDownloadZip(filenames) {
    try {
      const response = await api.post('/api/batch-download', {
        filenames
      }, {
        responseType: 'blob'  // 重要：指定响应类型为blob
      });

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // 从响应头获取文件名，如果没有则使用默认名称
      const contentDisposition = response.headers['content-disposition'];
      let filename = `voice_files_${Date.now()}.zip`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // 清理URL对象
      window.URL.revokeObjectURL(url);
      
      return {
        success: true,
        filename: filename,
        message: 'ZIP文件下载成功'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // 默认语言列表
  getDefaultLanguages() {
    return [
      { code: 'zh', name: '中文' },
      { code: 'en', name: '英文' },
      { code: 'ja', name: '日文' },
      { code: 'ko', name: '韩文' },
      { code: 'auto', name: '自动检测' }
    ];
  }

  // 默认语音类型
  getDefaultVoices() {
    return [
      { code: 'girl', name: '女声', gender: 'female' },
      { code: 'boy', name: '男声', gender: 'male' },
      { code: 'danbao', name: '蛋宝', gender: 'neutral' },
      { code: 'aitong', name: '艾彤', gender: 'female' }
    ];
  }
}

// 导出API服务实例
export default new APIService(); 