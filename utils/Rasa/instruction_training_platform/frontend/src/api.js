import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8081',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // 解决跨域问题
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    console.log('发送请求:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    console.log('收到响应:', response.status, response.config.url);
    return response;
  },
  (error) => {
    // 对响应错误做点什么
    console.error('响应错误:', error.response?.status, error.response?.data);
    
    // 统一错误处理
    if (error.response?.status === 500) {
      console.error('服务器内部错误');
    } else if (error.response?.status === 404) {
      console.error('请求的资源不存在');
    } else if (error.response?.status === 503) {
      console.error('服务不可用');
    }
    
    return Promise.reject(error);
  }
);

// API 接口定义
export const intentAPI = {
  // 获取意图列表
  getIntents: (params = {}) => api.get('/api/intents/', { params }),
  
  // 获取意图详情
  getIntent: (id) => api.get(`/api/intents/${id}`),
  
  // 创建意图
  createIntent: (data) => api.post('/api/intents', data),
  
  // 更新意图
  updateIntent: (id, data) => api.put(`/api/intents/${id}`, data),
  
  // 删除意图
  deleteIntent: (id) => api.delete(`/api/intents/${id}`),
  
  // 获取所有相似问（包含意图信息）
  getAllUtterances: () => api.get('/api/intents/utterances/all'),
  
  // 获取相似问
  getUtterances: (intentId) => api.get(`/api/intents/${intentId}/utterances`),
  
  // 创建相似问
  createUtterance: (intentId, data) => api.post(`/api/intents/${intentId}/utterances`, data),
  
  // 更新相似问
  updateUtterance: (id, data) => api.put(`/api/intents/utterances/${id}`, data),
  
  // 删除相似问
  deleteUtterance: (id) => api.delete(`/api/intents/utterances/${id}`),
  
  // 获取话术
  getResponses: (intentId) => api.get(`/api/intents/${intentId}/responses`),
  
  // 创建话术
  createResponse: (intentId, data) => api.post(`/api/intents/${intentId}/responses`, data),
  
  // 更新话术
  updateResponse: (id, data) => api.put(`/api/intents/responses/${id}`, data),
  
  // 删除话术
  deleteResponse: (id) => api.delete(`/api/intents/responses/${id}`),
};

export const rasaAPI = {
  // 语义理解预测
  predict: (text) => api.post('/api/rasa/predict', { text }),
  
  // 触发模型训练
  train: (data) => api.post('/api/rasa/train', data),
  
  // 检查 Rasa 服务状态
  getStatus: () => api.get('/api/rasa/status'),
  
  // 重新加载模型
  reloadModel: () => api.post('/api/rasa/reload-model'),
  
  // 获取训练数据
  getTrainingData: () => api.get('/api/rasa/training-data'),
};

export const toolsAPI = {
  // 批量测试
  batchTest: (data) => api.post('/api/tools/batch-test', data),
  
  // 数据上传
  uploadData: (data) => api.post('/api/tools/upload-data', data),
  
  // 文件上传
  uploadFile: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/tools/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // 批量测试文件上传 - 专门用于测试数据上传和解析
  uploadBatchTestFile: (formData) => {
    return api.post('/api/tools/upload-batch-test-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 增加超时时间，因为文件解析可能需要较长时间
    });
  },
  
  // 数据导出
  exportData: (format = 'rasa') => api.get('/api/tools/export-data', { params: { format } }),
  
  // 获取模型列表
  getModels: (params = {}) => api.get('/api/tools/models', { params }),
  
  // 获取当前激活模型
  getActiveModel: () => api.get('/api/tools/models/active'),
  
  // 激活模型
  activateModel: (modelId) => api.post(`/api/tools/models/${modelId}/activate`),
  
  // 获取训练任务状态
  getTrainingTask: (taskId) => api.get(`/api/tools/training-tasks/${taskId}`),
  
  // 获取系统信息
  getSystemInfo: () => api.get('/api/tools/system-info'),
  
  // 上传记录相关API
  // 获取上传记录列表
  getUploadRecords: (params = {}) => api.get('/api/tools/upload-records', { params }),
  
  // 获取上传记录详情
  getUploadRecordDetail: (recordId) => api.get(`/api/tools/upload-records/${recordId}`),
  
  // 删除上传记录
  deleteUploadRecord: (recordId) => api.delete(`/api/tools/upload-records/${recordId}`),
  
  // 下载上传记录的解析数据
  downloadUploadRecordData: (recordId) => api.get(`/api/tools/upload-records/${recordId}/download`),
  
  // 批量测试记录相关API
  // 获取批量测试记录列表
  getBatchTestRecords: (params = {}) => api.get('/api/tools/batch-test-records', { params }),
  
  // 获取最新的批量测试记录
  getLatestBatchTestRecord: () => api.get('/api/tools/batch-test-records/latest'),
  
  // 获取批量测试记录详情
  getBatchTestRecordDetail: (recordId) => api.get(`/api/tools/batch-test-records/${recordId}`),
  
  // 删除批量测试记录
  deleteBatchTestRecord: (recordId) => api.delete(`/api/tools/batch-test-records/${recordId}`),
  
  // 更新批量测试记录
  updateBatchTestRecord: (recordId, data) => api.put(`/api/tools/batch-test-records/${recordId}`, data),
};

export default api;

