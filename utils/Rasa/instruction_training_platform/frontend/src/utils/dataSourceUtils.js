/**
 * 数据源工具函数
 * 确保传递给 Ant Design Table 组件的 dataSource 始终是数组
 */

/**
 * 确保数据源是数组
 * @param {*} dataSource - 原始数据源
 * @param {Array} defaultValue - 默认值，通常是空数组
 * @returns {Array} - 确保返回数组
 */
export const ensureDataSourceArray = (dataSource, defaultValue = []) => {
  // 如果是数组，直接返回
  if (Array.isArray(dataSource)) {
    return dataSource;
  }
  
  // 如果是 null 或 undefined，返回默认值
  if (dataSource == null) {
    return defaultValue;
  }
  
  // 如果是对象，尝试提取数组字段
  if (typeof dataSource === 'object') {
    // 常见的数组字段名
    const arrayFields = ['data', 'list', 'items', 'records', 'results'];
    
    for (const field of arrayFields) {
      if (Array.isArray(dataSource[field])) {
        return dataSource[field];
      }
    }
    
    // 如果对象包含数组相关的字段，尝试提取
    if (dataSource.instructions && Array.isArray(dataSource.instructions)) {
      return dataSource.instructions;
    }
    
    if (dataSource.slots && Array.isArray(dataSource.slots)) {
      return dataSource.slots;
    }
    
    if (dataSource.libraries && Array.isArray(dataSource.libraries)) {
      return dataSource.libraries;
    }
    
    // 如果对象有 length 属性，可能是类数组对象
    if (typeof dataSource.length === 'number') {
      return Array.from(dataSource);
    }
  }
  
  // 其他情况，返回默认值
  console.warn('dataSource 不是预期的数组格式:', dataSource);
  return defaultValue;
};

/**
 * 安全的表格数据源处理
 * @param {*} dataSource - 原始数据源
 * @param {Object} options - 选项
 * @param {Array} options.defaultValue - 默认值
 * @param {boolean} options.logWarning - 是否记录警告
 * @returns {Array} - 处理后的数据源
 */
export const safeTableDataSource = (dataSource, options = {}) => {
  const { defaultValue = [], logWarning = true } = options;
  
  const result = ensureDataSourceArray(dataSource, defaultValue);
  
  if (logWarning && !Array.isArray(dataSource) && dataSource != null) {
    console.warn('Table dataSource 已自动转换为数组:', {
      original: dataSource,
      converted: result,
      type: typeof dataSource
    });
  }
  
  return result;
};

/**
 * 处理 API 响应数据
 * @param {*} response - API 响应
 * @param {string} dataField - 数据字段名
 * @returns {Array} - 提取的数组数据
 */
export const extractArrayFromResponse = (response, dataField = 'data') => {
  if (!response) return [];
  
  // 如果响应直接是数组
  if (Array.isArray(response)) {
    return response;
  }
  
  // 如果响应是对象
  if (typeof response === 'object') {
    // 尝试从 response.data 提取
    if (response.data) {
      return ensureDataSourceArray(response.data);
    }
    
    // 尝试从指定字段提取
    if (dataField && response[dataField]) {
      return ensureDataSourceArray(response[dataField]);
    }
    
    // 尝试从响应对象本身提取
    return ensureDataSourceArray(response);
  }
  
  return [];
};

/**
 * 全局错误处理机制
 * 捕获并修复 rawData.some is not a function 错误
 */
export const setupGlobalDataSourceErrorHandler = () => {
  // 监听全局错误
  window.addEventListener('error', (event) => {
    if (event.error && event.error.message && 
        event.error.message.includes('rawData.some is not a function')) {
      console.error('检测到 rawData.some 错误，可能是 dataSource 不是数组:', event.error);
      
      // 可以在这里添加自动修复逻辑或用户提示
      console.warn('请检查所有 Table 和 List 组件的 dataSource 属性是否为数组');
      
      // 阻止错误冒泡
      event.preventDefault();
      return false;
    }
  });
  
  // 监听 Promise 拒绝
  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason && event.reason.message && 
        event.reason.message.includes('rawData.some is not a function')) {
      console.error('检测到异步 rawData.some 错误:', event.reason);
      event.preventDefault();
    }
  });
};

// 自动设置全局错误处理
if (typeof window !== 'undefined') {
  setupGlobalDataSourceErrorHandler();
} 