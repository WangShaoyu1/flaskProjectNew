import React, { useState, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography, Spin, Alert } from 'antd';
import {
  DashboardOutlined,
  BulbOutlined,
  RobotOutlined,
  ToolOutlined,
  SettingOutlined,
  ApiOutlined
} from '@ant-design/icons';

// 导入页面组件
import Dashboard from './pages/Dashboard';
import IntentManagement from './pages/IntentManagement';
import Testing from './pages/Testing';
import Training from './pages/Training';
import Tools from './pages/Tools';
import Settings from './pages/Settings';

import { rasaAPI } from './api';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const App = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [rasaStatus, setRasaStatus] = useState('checking');
  const [loading, setLoading] = useState(true);
  const location = useLocation();

  // 菜单项配置
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/intents',
      icon: <BulbOutlined />,
      label: '意图管理',
    },
    {
      key: '/training',
      icon: <RobotOutlined />,
      label: '模型训练',
    },
    {
      key: '/testing',
      icon: <ApiOutlined />,
      label: '测试中心',
    },
    {
      key: '/tools',
      icon: <ToolOutlined />,
      label: '工具箱',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  // 检查 Rasa 服务状态
  const checkRasaStatus = async () => {
    try {
      const response = await rasaAPI.getStatus();
      setRasaStatus(response.data.status);
    } catch (error) {
      console.error('检查 Rasa 状态失败:', error);
      setRasaStatus('unavailable');
    }
  };

  useEffect(() => {
    const initApp = async () => {
      setLoading(true);
      await checkRasaStatus();
      setLoading(false);
    };

    initApp();

    // 定期检查 Rasa 状态
    const statusInterval = setInterval(checkRasaStatus, 30000);

    return () => clearInterval(statusInterval);
  }, []);

  // 获取当前页面标题
  const getCurrentPageTitle = () => {
    const currentItem = menuItems.find(item => item.key === location.pathname);
    return currentItem ? currentItem.label : '指令训练平台';
  };

  // 渲染 Rasa 状态指示器
  const renderRasaStatus = () => {
    const statusConfig = {
      available: { color: '#52c41a', text: 'Rasa 服务正常' },
      unavailable: { color: '#ff4d4f', text: 'Rasa 服务不可用' },
      checking: { color: '#1890ff', text: '检查中...' }
    };

    const config = statusConfig[rasaStatus] || statusConfig.checking;

    return (
      <div className="status-indicator" style={{ color: config.color }}>
        <div 
          style={{ 
            width: 8, 
            height: 8, 
            borderRadius: '50%', 
            backgroundColor: config.color 
          }} 
        />
        {config.text}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="正在初始化应用..." />
      </div>
    );
  }

  return (
    <Layout className="app-container" style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
        width={250}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          borderBottom: '1px solid #303030'
        }}>
          <Title 
            level={4} 
            style={{ 
              color: 'white', 
              margin: 0,
              fontSize: collapsed ? '16px' : '18px'
            }}
          >
            {collapsed ? 'ITP' : '指令训练平台'}
          </Title>
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => {
            window.history.pushState(null, '', key);
            window.dispatchEvent(new PopStateEvent('popstate'));
          }}
        />
      </Sider>

      <Layout>
        <Header style={{ 
          background: 'white', 
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <Title level={3} style={{ margin: 0 }}>
            {getCurrentPageTitle()}
          </Title>
          
          {renderRasaStatus()}
        </Header>

        <Content className="main-content">
          {rasaStatus === 'unavailable' && (
            <Alert
              message="Rasa 服务不可用"
              description="请确保 Rasa 服务正在运行在 http://localhost:5005，某些功能可能无法正常使用。"
              type="warning"
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}

          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/intents" element={<IntentManagement />} />
            <Route path="/training" element={<Training />} />
            <Route path="/testing" element={<Testing />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;

