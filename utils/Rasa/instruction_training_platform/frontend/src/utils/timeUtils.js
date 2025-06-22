// 时间处理工具函数

/**
 * 格式化时间为当地时间显示
 * @param {string|Date} dateTime - 时间字符串或Date对象
 * @param {object} options - 格式化选项
 * @returns {string} 格式化后的时间字符串
 */
export const formatLocalTime = (dateTime, options = {}) => {
  if (!dateTime) return '-';
  
  try {
    let date;
    
    // 处理不同的输入格式
    if (typeof dateTime === 'string') {
      // 如果是UTC时间字符串，直接解析
      if (dateTime.endsWith('Z') || dateTime.includes('+')) {
        date = new Date(dateTime);
      } else {
        // 如果没有时区信息，假设是UTC时间，添加Z后缀
        date = new Date(dateTime + (dateTime.includes('T') ? 'Z' : 'T00:00:00Z'));
      }
    } else {
      date = new Date(dateTime);
    }
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn('Invalid date:', dateTime);
      return '-';
    }
    
    // 默认格式化选项
    const defaultOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
    
    const formatOptions = { ...defaultOptions, ...options };
    
    return date.toLocaleString('zh-CN', formatOptions);
  } catch (error) {
    console.error('Error formatting date:', error, dateTime);
    return '-';
  }
};

/**
 * 格式化时间为短格式（年月日）
 * @param {string|Date} dateTime - 时间字符串或Date对象
 * @returns {string} 格式化后的日期字符串
 */
export const formatLocalDate = (dateTime) => {
  return formatLocalTime(dateTime, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

/**
 * 格式化时间为文件名格式（用于下载文件命名）
 * @param {string|Date} dateTime - 时间字符串或Date对象
 * @returns {string} 格式化后的时间字符串（去除特殊字符）
 */
export const formatTimeForFilename = (dateTime) => {
  return formatLocalTime(dateTime, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/[\/\s:]/g, '');
};

/**
 * 获取当前时间的格式化字符串
 * @returns {string} 当前时间的格式化字符串
 */
export const getCurrentTimeString = () => {
  return formatLocalTime(new Date());
};

/**
 * 生成默认的测试名称：年月日+第几次测试
 * @param {number} testCount - 测试序号
 * @returns {string} 默认测试名称
 */
export const generateDefaultTestName = (testCount = 1) => {
  const now = new Date();
  const dateStr = formatLocalDate(now).replace(/\//g, '');
  return `${dateStr}第${testCount}次测试`;
}; 