import React, { useState, useEffect } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu, Typography, Spin, Alert, Badge, App } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  MessageOutlined,
  BranchesOutlined,
  SettingOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { applyTheme } from './styles/colors';

// 导入新版本页面组件
import DashboardV2 from './pages-v2/DashboardV2';
import LibraryManagement from './pages-v2/LibraryManagement';
import InstructionManagement from './pages-v2/InstructionManagement';
import VersionManagement from './pages-v2/VersionManagement';
import SettingsV2 from './pages-v2/SettingsV2';

import { systemAPI } from './api-v2';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

const AppV2 = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState('checking');
  const [loading, setLoading] = useState(true);
  const [currentLibrary, setCurrentLibrary] = useState(null);
  const location = useLocation();
  const navigate = useNavigate();

  // 菜单项配置 - 已优化，移除词槽管理、指令测试、模型训练
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/libraries',
      icon: <DatabaseOutlined />,
      label: '指令库管理',
    },
    {
      key: '/instructions',
      icon: <MessageOutlined />,
      label: '指令数据管理',
    },
    {
      key: '/versions',
      icon: <BranchesOutlined />,
      label: '版本管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  // 检查系统状态
  const checkSystemStatus = async () => {
    try {
      const response = await systemAPI.healthCheck();
      setSystemStatus('healthy');
    } catch (error) {
      console.error('系统健康检查失败:', error);
      setSystemStatus('unhealthy');
    }
  };

  useEffect(() => {
    const initApp = async () => {
      setLoading(true);
      
      // 初始化主题
      const savedTheme = localStorage.getItem('buttonTheme') || 'classic';
      applyTheme(savedTheme);
      
      // 获取当前指令库
      const savedLibrary = localStorage.getItem('currentLibrary');
      if (savedLibrary) {
        try {
          setCurrentLibrary(JSON.parse(savedLibrary));
        } catch (e) {
          localStorage.removeItem('currentLibrary');
        }
      }
      
      await checkSystemStatus();
      setLoading(false);
    };

    initApp();

    // 定期检查系统状态
    const statusInterval = setInterval(checkSystemStatus, 60000);

    return () => clearInterval(statusInterval);
  }, []);

  // 获取当前页面标题
  const getCurrentPageTitle = () => {
    const currentItem = menuItems.find(item => item.key === location.pathname);
    const title = currentItem ? currentItem.label : '智能对话训练平台 v2.0.0';
    
    // 如果有当前指令库，显示指令库名称
    if (currentLibrary && location.pathname !== '/' && location.pathname !== '/libraries') {
      return `${title} - ${currentLibrary.name}`;
    }
    
    return title;
  };

  // 渲染系统状态指示器
  const renderSystemStatus = () => {
    const statusConfig = {
      healthy: { color: '#52c41a', text: '系统正常', status: 'success' },
      unhealthy: { color: '#ff4d4f', text: '系统异常', status: 'error' },
      checking: { color: '#1890ff', text: '检查中...', status: 'processing' }
    };

    const config = statusConfig[systemStatus] || statusConfig.checking;

    return (
      <div className="status-container" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {/* 指令库指示器 */}
        {currentLibrary && (
          <div className="library-indicator" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Badge color="#1890ff" />
            <span style={{ color: '#666' }}>
              当前指令库: <strong>{currentLibrary.name}</strong>
            </span>
          </div>
        )}
        
        {/* 系统状态指示器 */}
        <div className="status-indicator" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Badge status={config.status} />
          <span style={{ color: config.color }}>{config.text}</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading-container" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        backgroundColor: '#f0f2f5'
      }}>
        <Spin size="large" tip="正在初始化应用...">
          <div style={{ minHeight: '200px', minWidth: '200px' }} />
        </Spin>
      </div>
    );
  }

  return (
    <App>
      <Layout className={`app-container ${collapsed ? 'collapsed' : ''}`}>
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          theme="dark"
          width={250}
          collapsedWidth={80}
        >
          <div style={{ 
            height: 64, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            borderBottom: '1px solid #303030'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ThunderboltOutlined 
                style={{ 
                  color: '#1890ff', 
                  fontSize: collapsed ? '20px' : '24px',
                  marginRight: collapsed ? 0 : 8
                }} 
              />
              <Title 
                level={4} 
                style={{ 
                  color: 'white', 
                  margin: 0,
                  fontSize: collapsed ? '14px' : '16px'
                }}
              >
                {collapsed ? 'ITP' : '智能训练平台'}
              </Title>
              {!collapsed && (
                <Badge 
                  count="v2.0" 
                  style={{ 
                    backgroundColor: '#52c41a', 
                    fontSize: '10px',
                    minWidth: '32px',
                    height: '16px',
                    lineHeight: '16px'
                  }} 
                />
              )}
            </div>
          </div>
          
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => {
              navigate(key);
            }}
          />
        </Sider>

        <Layout>
          <Header style={{ 
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#fff',
            borderBottom: '1px solid #f0f0f0'
          }}>
            <Title level={3} style={{ margin: 0 }}>
              {getCurrentPageTitle()}
            </Title>
            
            {renderSystemStatus()}
          </Header>

          <Content className="main-content" style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
            {systemStatus === 'unhealthy' && (
              <Alert
                message="系统连接异常：无法连接到后端服务（http://localhost:8001），某些功能可能无法正常使用。"
                type="warning"
                showIcon
                style={{ marginBottom: 24 }}
              />
            )}

            {!currentLibrary && location.pathname !== '/' && location.pathname !== '/libraries' && (
              <Alert
                message="请选择指令库"
                description="请先在指令库管理页面选择或创建一个指令库，然后才能使用其他功能。"
                type="info"
                showIcon
                action={
                  <span 
                    style={{ color: '#1890ff', cursor: 'pointer' }}
                    onClick={() => navigate('/libraries')}
                  >
                    前往指令库管理
                  </span>
                }
                style={{ marginBottom: 24 }}
              />
            )}

            <Routes>
              <Route path="/" element={<DashboardV2 />} />
              <Route 
                path="/libraries" 
                element={<LibraryManagement onLibrarySelect={setCurrentLibrary} navigate={navigate} />} 
              />
              <Route path="/instructions" element={<InstructionManagement currentLibrary={currentLibrary} />} />
              <Route path="/versions" element={<VersionManagement currentLibrary={currentLibrary} />} />
              <Route path="/settings" element={<SettingsV2 />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </App>
  );
};

export default AppV2; 