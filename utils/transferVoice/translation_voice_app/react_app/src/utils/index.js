// 语速转换工具
export const convertSpeechRate = (voiceType, uiSpeed) => {
  // 艾彤音色使用阿里云TTS，需要转换语速格式
  if (voiceType === 'aitong') {
    // 将0.5-2.0倍速转换为阿里云TTS的-500~500格式（整数）
    // 1.0倍速对应0，0.5倍速对应-500，2.0倍速对应500
    const convertedValue = Math.round((uiSpeed - 1.0) * 500);
    // 确保返回整数，范围限制在-500到500之间
    return Math.max(-500, Math.min(500, convertedValue));
  }
  return uiSpeed;
};

// 文件大小格式化
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 时长格式化
export const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '未知';
  
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  
  return `${mins}:${secs.toString().padStart(2, '0')}`;
};

// 防抖函数
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// 节流函数
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// 复制到剪贴板
export const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (error) {
    console.error('复制失败:', error);
    return false;
  }
};

// 从剪贴板粘贴
export const pasteFromClipboard = async () => {
  try {
    const text = await navigator.clipboard.readText();
    return text;
  } catch (error) {
    console.error('粘贴失败:', error);
    return null;
  }
};

// 下载文件
export const downloadFile = (url, filename) => {
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 播放音频
export const playAudio = (audioUrl) => {
  return new Promise((resolve, reject) => {
    const audio = new Audio(audioUrl);
    
    audio.addEventListener('loadstart', () => {
      console.log('音频开始加载');
    });
    
    audio.addEventListener('canplay', () => {
      console.log('音频可以播放');
      audio.play().then(resolve).catch(reject);
    });
    
    audio.addEventListener('error', (e) => {
      console.error('音频加载错误:', e);
      reject(new Error('音频加载失败'));
    });
    
    audio.addEventListener('ended', () => {
      console.log('音频播放完成');
    });
    
    audio.load();
  });
};

// 本地存储工具
export const storage = {
  set: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error('存储失败:', error);
      return false;
    }
  },
  
  get: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error('读取存储失败:', error);
      return defaultValue;
    }
  },
  
  remove: (key) => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error('删除存储失败:', error);
      return false;
    }
  },
  
  clear: () => {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('清空存储失败:', error);
      return false;
    }
  }
}; 