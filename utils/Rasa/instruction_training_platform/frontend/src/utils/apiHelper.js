/**
 * API响应处理工具
 * 统一处理后端返回的 code、msg、data 格式
 */

// 错误码常量
export const ERROR_CODES = {
    SUCCESS: '000000',
    SYSTEM_ERROR: '999999',
    PARAM_ERROR: '400001',
    NOT_FOUND: '404001',
    ALREADY_EXISTS: '409001',
    UNAUTHORIZED: '401001',
    FORBIDDEN: '403001',
    VALIDATION_ERROR: '422001',
    DATABASE_ERROR: '500001',
    EXTERNAL_API_ERROR: '500002'
};

/**
 * 处理API响应
 * @param {Object} response - API响应对象
 * @returns {any} - 成功时返回data，失败时抛出异常
 */
export const handleApiResponse = (response) => {
    if (!response) {
        throw new Error('API响应为空');
    }
    
    // 如果响应已经是新格式
    if (response.code !== undefined) {
        if (response.code === ERROR_CODES.SUCCESS) {
            return response.data;
        } else {
            const error = new Error(response.msg || '请求失败');
            error.code = response.code;
            error.data = response.data;
            throw error;
        }
    }
    
    // 兼容旧格式：直接返回响应数据
    return response;
};

/**
 * 显示API错误消息
 * @param {Error} error - 错误对象
 * @param {Function} messageApi - antd message API
 */
export const showApiError = (error, messageApi) => {
    let errorMessage = '操作失败';
    
    if (error.code) {
        // 根据错误码显示不同的消息
        switch (error.code) {
            case ERROR_CODES.PARAM_ERROR:
                errorMessage = `参数错误: ${error.message}`;
                break;
            case ERROR_CODES.NOT_FOUND:
                errorMessage = `资源不存在: ${error.message}`;
                break;
            case ERROR_CODES.ALREADY_EXISTS:
                errorMessage = `资源已存在: ${error.message}`;
                break;
            case ERROR_CODES.UNAUTHORIZED:
                errorMessage = `未授权访问: ${error.message}`;
                break;
            case ERROR_CODES.FORBIDDEN:
                errorMessage = `禁止访问: ${error.message}`;
                break;
            case ERROR_CODES.VALIDATION_ERROR:
                errorMessage = `数据验证失败: ${error.message}`;
                break;
            case ERROR_CODES.DATABASE_ERROR:
                errorMessage = `数据库错误: ${error.message}`;
                break;
            case ERROR_CODES.EXTERNAL_API_ERROR:
                errorMessage = `外部API错误: ${error.message}`;
                break;
            case ERROR_CODES.SYSTEM_ERROR:
            default:
                errorMessage = `系统错误: ${error.message}`;
                break;
        }
    } else {
        errorMessage = error.message || '未知错误';
    }
    
    if (messageApi) {
        messageApi.error(errorMessage);
    } else {
        console.error(errorMessage);
    }
};

/**
 * 显示API成功消息
 * @param {string} message - 成功消息
 * @param {Function} messageApi - antd message API
 */
export const showApiSuccess = (message, messageApi) => {
    if (messageApi) {
        messageApi.success(message || '操作成功');
    } else {
        console.log(message || '操作成功');
    }
};

// 默认导出
export default {
    handleApiResponse,
    showApiError,
    showApiSuccess,
    ERROR_CODES
}; 