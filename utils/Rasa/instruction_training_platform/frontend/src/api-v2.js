import axios from 'axios';

// 创建 axios 实例 - v2.0.0 API
const apiV2 = axios.create({
  baseURL: process.env.REACT_APP_API_V2_URL || 'http://localhost:8001',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

// 请求拦截器
apiV2.interceptors.request.use(
  (config) => {
    console.log('V2 API请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('V2 API请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiV2.interceptors.response.use(
  (response) => {
    console.log('V2 API响应:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('V2 API响应错误:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// ===== 指令库母版管理API =====
export const libraryAPI = {
  // 获取指令库列表
  getLibraries: (params = {}) => apiV2.get('/api/v2/library/list', { params }),
  
  // 创建指令库
  createLibrary: (data) => apiV2.post('/api/v2/library/create', data),
  
  // 获取指令库详情
  getLibrary: (libraryId) => apiV2.get(`/api/v2/library/${libraryId}`),
  
  // 更新指令库
  updateLibrary: (libraryId, data) => apiV2.put(`/api/v2/library/${libraryId}`, data),
  
  // 删除指令库
  deleteLibrary: (libraryId) => apiV2.delete(`/api/v2/library/${libraryId}`),
  
  // 获取指令库统计
  getLibraryStats: (libraryId) => apiV2.get(`/api/v2/library/${libraryId}/stats`),
};

// ===== 指令数据管理API =====
export const instructionAPI = {
  // 获取指令列表
  getInstructions: (params = {}) => apiV2.get('/api/v2/instruction/list', { params }),
  
  // 创建指令
  createInstruction: (data) => apiV2.post('/api/v2/instruction/create', data),
  
  // 获取指令详情
  getInstruction: (instructionId) => apiV2.get(`/api/v2/instruction/${instructionId}`),
  
  // 更新指令
  updateInstruction: (instructionId, data) => apiV2.put(`/api/v2/instruction/${instructionId}`, data),
  
  // 删除指令
  deleteInstruction: (instructionId) => apiV2.delete(`/api/v2/instruction/${instructionId}`),
  
  // 批量导入指令
  batchImport: (formData) => apiV2.post('/api/v2/instruction/batch-import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  // 下载指令导入模板
  downloadTemplate: () => apiV2.get('/api/v2/instruction/template', { responseType: 'blob' }),
  
  // 获取指令分类
  getCategories: (libraryId) => apiV2.get('/api/v2/instruction/categories', { params: { library_id: libraryId } }),
  
  // 获取相似问列表
  getSimilarQuestions: (instructionId) => apiV2.get(`/api/v2/instruction/${instructionId}/similar-questions`),
  
  // 添加相似问
  addSimilarQuestion: (instructionId, data) => apiV2.post(`/api/v2/instruction/${instructionId}/similar-questions`, data),
  
  // 更新相似问
  updateSimilarQuestion: (instructionId, questionId, data) => apiV2.put(`/api/v2/instruction/${instructionId}/similar-questions/${questionId}`, data),
  
  // 删除相似问
  deleteSimilarQuestion: (instructionId, questionId) => apiV2.delete(`/api/v2/instruction/${instructionId}/similar-questions/${questionId}`),
};

// ===== 词槽管理API =====
export const slotAPI = {
  // 获取词槽类型
  getSlotTypes: () => apiV2.get('/api/v2/slots/slot-types'),
  
  // 获取词槽列表
  getSlots: (params = {}) => apiV2.get('/api/v2/slots/list', { params }),
  
  // 创建词槽
  createSlot: (data) => apiV2.post('/api/v2/slots/create', data),
  
  // 获取词槽详情
  getSlot: (slotId) => apiV2.get(`/api/v2/slots/${slotId}`),
  
  // 更新词槽
  updateSlot: (slotId, data) => apiV2.put(`/api/v2/slots/${slotId}`, data),
  
  // 删除词槽
  deleteSlot: (slotId) => apiV2.delete(`/api/v2/slots/${slotId}`),
  
  // 获取词槽值列表
  getSlotValues: (slotId, params = {}) => apiV2.get(`/api/v2/slots/${slotId}/values`, { params }),
  
  // 添加词槽值
  addSlotValue: (slotId, data) => apiV2.post(`/api/v2/slots/${slotId}/values`, data),
  
  // 更新词槽值
  updateSlotValue: (slotId, valueId, data) => apiV2.put(`/api/v2/slots/${slotId}/values/${valueId}`, data),
  
  // 删除词槽值
  deleteSlotValue: (slotId, valueId) => apiV2.delete(`/api/v2/slots/${slotId}/values/${valueId}`),
  
  // 批量导入词槽值
  batchImportSlotValues: (slotId, data) => apiV2.post(`/api/v2/slots/${slotId}/values/batch-import`, data),
  
  // 批量导入词槽
  batchImport: (formData) => apiV2.post('/api/v2/slots/batch-import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  // 下载词槽导入模板
  downloadTemplate: () => apiV2.get('/api/v2/slots/download-template', { responseType: 'blob' }),
  
  // 获取关联指令
  getRelatedInstructions: (slotId) => apiV2.get(`/api/v2/slots/${slotId}/related-instructions`),
  
  // 获取词槽汇总
  getSlotSummary: (libraryId) => apiV2.get(`/api/v2/slots/library/${libraryId}/summary`),
  
  // 初始化系统词槽
  initSystemSlots: (libraryId) => apiV2.post(`/api/v2/slots/init-system-slots?library_id=${libraryId}`, {}),
};

// ===== 指令测试API =====
export const testAPI = {
  // 单条指令测试
  singleTest: (data) => apiV2.post('/api/v2/test/single', data),
  
  // 批量指令测试
  batchTest: (formData) => apiV2.post('/api/v2/test/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  // 下载测试模板
  downloadTemplate: () => apiV2.get('/api/v2/test/template/download', { responseType: 'blob' }),
  
  // 获取测试记录列表
  getTestRecords: (params = {}) => apiV2.get('/api/v2/test/records', { params }),
  
  // 获取测试记录详情
  getTestRecordDetail: (recordId) => apiV2.get(`/api/v2/test/records/${recordId}`),
  
  // 删除测试记录
  deleteTestRecord: (recordId) => apiV2.delete(`/api/v2/test/records/${recordId}`),
  
  // 导出测试结果
  exportResults: (recordId) => apiV2.get(`/api/v2/test/records/${recordId}/export`, { responseType: 'blob' }),
  
  // 获取测试汇总
  getTestSummary: (libraryId) => apiV2.get(`/api/v2/test/library/${libraryId}/summary`),
};

// ===== 模型训练API =====
export const trainingAPI = {
  // 开始训练
  startTraining: (data) => apiV2.post('/api/v2/training/start', data),
  
  // 获取训练状态
  getTrainingStatus: (trainingRecordId) => apiV2.get(`/api/v2/training/status/${trainingRecordId}`),
  
  // 获取训练记录列表
  getTrainingRecords: (params = {}) => apiV2.get('/api/v2/training/records', { params }),
  
  // 获取训练记录详情
  getTrainingRecordDetail: (recordId) => apiV2.get(`/api/v2/training/records/${recordId}`),
  
  // 获取训练日志
  getTrainingLogs: (recordId) => apiV2.get(`/api/v2/training/records/${recordId}/logs`),
  
  // 激活训练记录
  activateTrainingRecord: (recordId) => apiV2.post(`/api/v2/training/records/${recordId}/activate`),
  
  // 删除训练记录
  deleteTrainingRecord: (recordId) => apiV2.delete(`/api/v2/training/records/${recordId}`),
  
  // 获取训练汇总
  getTrainingSummary: (libraryId) => apiV2.get(`/api/v2/training/library/${libraryId}/summary`),
  
  // 取消训练
  cancelTraining: (recordId) => apiV2.post(`/api/v2/training/cancel/${recordId}`),
  
  // 清除所有训练记录
  clearAllTrainingRecords: () => apiV2.post('/api/v2/training/clear-all'),
  
  // 获取训练系统状态
  getTrainingSystemStatus: () => apiV2.get('/api/v2/training/status'),
};

// ===== 版本管理API =====
export const versionAPI = {
  // 获取版本列表
  getVersions: (params = {}) => apiV2.get('/api/v2/version/list', { params }),
  
  // 获取版本详情
  getVersionDetail: (versionId) => apiV2.get(`/api/v2/version/detail/${versionId}`),
  
  // 激活版本
  activateVersion: (versionId) => apiV2.post(`/api/v2/version/activate/${versionId}`),
  
  // 获取当前激活版本
  getActiveVersion: (libraryId) => apiV2.get(`/api/v2/version/active/${libraryId}`),
  
  // 版本对比
  compareVersions: (data) => apiV2.post('/api/v2/version/compare', data),
  
  // 删除版本
  deleteVersion: (versionId, force = false) => apiV2.delete(`/api/v2/version/${versionId}?force=${force}`),
  
  // 获取版本统计
  getVersionStatistics: (libraryId) => apiV2.get(`/api/v2/version/statistics/${libraryId}`),
};

// ===== 系统API =====
export const systemAPI = {
  // 健康检查
  healthCheck: () => apiV2.get('/api/health'),
  
  // 获取版本信息
  getVersion: () => apiV2.get('/api/version'),
  
  // 系统状态
  getSystemStatus: () => apiV2.get('/'),
};

// 工具函数
export const apiUtils = {
  // 处理文件上传
  uploadFile: (url, file, additionalData = {}, onProgress = null) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // 添加额外数据
    Object.keys(additionalData).forEach(key => {
      formData.append(key, additionalData[key]);
    });
    
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    };
    
    // 如果有进度回调
    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      };
    }
    
    return apiV2.post(url, formData, config);
  },
  
  // 错误处理
  handleError: (error, defaultMessage = '操作失败') => {
    const message = error.response?.data?.detail || error.message || defaultMessage;
    console.error('API错误:', message);
    return message;
  },
  
  // 构建查询参数
  buildParams: (params) => {
    const cleanParams = {};
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
        cleanParams[key] = params[key];
      }
    });
    return cleanParams;
  },
};

export default apiV2; 