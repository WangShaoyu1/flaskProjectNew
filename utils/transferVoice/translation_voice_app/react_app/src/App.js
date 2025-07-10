import React, { useState, useEffect } from 'react';
import { Layout, Typography, Space, Alert, Spin, message, Badge } from 'antd';
import { SoundOutlined, TranslationOutlined, HeartOutlined, CheckCircleOutlined, ExclamationCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import TranslationPanel from './components/TranslationPanel';
import VoiceSynthesis from './components/VoiceSynthesis';
import apiService from './services/api';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

function App() {
  const [translatedText, setTranslatedText] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [apiStatus, setApiStatus] = useState('loading');
  const [apiError, setApiError] = useState('');

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const result = await apiService.healthCheck();
      if (result.success) {
        setApiStatus('connected');
        // 去掉重复的连接成功消息
      } else {
        setApiStatus('error');
        setApiError(result.error);
        message.error(`API服务连接失败: ${result.error}`);
      }
    } catch (error) {
      setApiStatus('error');
      setApiError(error.message);
      message.error(`API服务连接失败: ${error.message}`);
    }
  };

  const handleTranslationChange = (text, source = '') => {
    setTranslatedText(text);
    if (source) {
      setSourceText(source);
    }
  };

  const getApiStatusAlert = () => {
    switch (apiStatus) {
      case 'loading':
        return (
          <Alert
            message="正在连接API服务..."
            type="info"
            showIcon
            icon={<Spin size="small" />}
            style={{ marginBottom: 16 }}
          />
        );
      case 'error':
        return (
          <Alert
            message="API服务连接失败"
            description={`错误信息: ${apiError}`}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
            action={
              <button onClick={checkApiHealth}>重试</button>
            }
          />
        );
      case 'connected':
        // 去掉API服务连接正常的Alert文本框
        return null;
      default:
        return null;
    }
  };

  const getApiStatusIndicator = () => {
    switch (apiStatus) {
      case 'loading':
        return (
          <Space>
            <LoadingOutlined style={{ color: '#1890ff' }} />
            <Text style={{ color: 'rgba(255, 255, 255, 0.85)', fontSize: '12px' }}>
              连接中...
            </Text>
          </Space>
        );
      case 'error':
        return (
          <Space style={{ cursor: 'pointer' }} onClick={checkApiHealth}>
            <Badge status="error" />
            <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
            <Text style={{ color: '#ff4d4f', fontSize: '12px' }}>
              API异常
            </Text>
          </Space>
        );
      case 'connected':
        return (
          <Space>
            <Badge status="success" />
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            <Text style={{ color: '#52c41a', fontSize: '12px' }}>
              API正常
            </Text>
          </Space>
        );
      default:
        return null;
    }
  };

  return (
    <div className="App">
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{ 
          background: 'linear-gradient(135deg, #9e9e9e 0%, #764ba2 100%)',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Space align='center'>
            <SoundOutlined style={{ fontSize: '24px', color: 'white',paddingTop: '24px' }} />
            <Title level={3} style={{ color: 'white', margin: 0 }}>
              翻译语音合成应用
            </Title>
          </Space>
          <Space size="large">
            {getApiStatusIndicator()}
          </Space>
        </Header>

        <Content style={{ 
          padding: '24px',
          background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
          minHeight: 'calc(100vh - 134px)'
        }}>
          <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            {getApiStatusAlert()}
            
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <TranslationPanel 
                onTranslationChange={handleTranslationChange}
              />
              
              <VoiceSynthesis 
                translatedText={translatedText}
                sourceText={sourceText}
              />
            </Space>
          </div>
        </Content>

        <Footer style={{ 
          textAlign: 'center',
          background: '#001529',
          color: 'rgba(255, 255, 255, 0.65)'
        }}>
          <Space>
            <TranslationOutlined />
            <Text style={{ color: 'rgba(255, 255, 255, 0.65)' }}>
              翻译语音合成应用 ©2024 Created by hero
            </Text>
            <HeartOutlined style={{ color: '#ff4d4f' }} />
          </Space>
        </Footer>
      </Layout>
    </div>
  );
}

export default App; 