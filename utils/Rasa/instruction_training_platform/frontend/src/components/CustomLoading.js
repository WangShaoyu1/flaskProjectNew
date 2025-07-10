import React from 'react';
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

const CustomLoading = ({ 
  visible = false, 
  text = "正在加载...", 
  description = "",
  size = "default" // small, default, large
}) => {
  if (!visible) return null;

  const antIcon = <LoadingOutlined style={{ fontSize: size === 'large' ? 48 : size === 'small' ? 24 : 36 }} spin />;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      flexDirection: 'column'
    }}>
      <Spin 
        indicator={antIcon} 
        size={size}
      />
      <div style={{ 
        marginTop: 16, 
        fontSize: '16px', 
        color: '#666',
        textAlign: 'center'
      }}>
        {text}
      </div>
      {description && (
        <div style={{ 
          marginTop: 8, 
          fontSize: '14px', 
          color: '#999',
          textAlign: 'center'
        }}>
          {description}
        </div>
      )}
    </div>
  );
};

export default CustomLoading; 