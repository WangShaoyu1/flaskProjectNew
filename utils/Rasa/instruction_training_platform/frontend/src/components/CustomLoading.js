import React from 'react';

const CustomLoading = ({ 
  visible = false, 
  text = "正在加载...", 
  description = "请稍候",
  size = "default" // small, default, large
}) => {
  if (!visible) return null;

  const getSpinnerSize = () => {
    switch (size) {
      case 'small': return { width: '32px', height: '32px', borderWidth: '3px' };
      case 'large': return { width: '64px', height: '64px', borderWidth: '5px' };
      default: return { width: '48px', height: '48px', borderWidth: '4px' };
    }
  };

  const spinnerStyle = getSpinnerSize();

  return (
    <div className="custom-fullscreen-loading">
      <div className="custom-loading-content">
        <div 
          className="custom-loading-spinner"
          style={spinnerStyle}
        />
        <div className="custom-loading-text">{text}</div>
        {description && (
          <div className="custom-loading-desc">{description}</div>
        )}
      </div>
    </div>
  );
};

export default CustomLoading; 