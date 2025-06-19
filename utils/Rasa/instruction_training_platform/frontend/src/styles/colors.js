// 按钮颜色主题配置
export const buttonThemes = {
  // 经典淡雅主题（当前使用）
  classic: {
    primary: {
      start: '#e3f2fd',
      end: '#bbdefb',
      hoverStart: '#bbdefb',
      hoverEnd: '#90caf9',
      text: '#1976d2',
      textHover: '#0d47a1'
    },
    success: {
      start: '#f1f8e9',
      end: '#dcedc8',
      hoverStart: '#dcedc8',
      hoverEnd: '#c5e1a5',
      text: '#388e3c',
      textHover: '#1b5e20'
    },
    warning: {
      start: '#fff8e1',
      end: '#ffecb3',
      hoverStart: '#ffecb3',
      hoverEnd: '#ffe082',
      text: '#f57c00',
      textHover: '#e65100'
    },
    info: {
      start: '#f3e5f5',
      end: '#e1bee7',
      hoverStart: '#e1bee7',
      hoverEnd: '#ce93d8',
      text: '#7b1fa2',
      textHover: '#4a148c'
    }
  },

  // 商务专业主题
  business: {
    primary: {
      start: '#e8f4fd',
      end: '#d1e9fc',
      hoverStart: '#d1e9fc',
      hoverEnd: '#a3d2f7',
      text: '#1565c0',
      textHover: '#0d47a1'
    },
    success: {
      start: '#e8f5e8',
      end: '#c8e6c9',
      hoverStart: '#c8e6c9',
      hoverEnd: '#a5d6a7',
      text: '#2e7d32',
      textHover: '#1b5e20'
    },
    warning: {
      start: '#fff3e0',
      end: '#ffe0b2',
      hoverStart: '#ffe0b2',
      hoverEnd: '#ffcc80',
      text: '#ef6c00',
      textHover: '#e65100'
    },
    info: {
      start: '#f1f8e9',
      end: '#dcedc8',
      hoverStart: '#dcedc8',
      hoverEnd: '#c5e1a5',
      text: '#689f38',
      textHover: '#33691e'
    }
  },

  // 现代科技主题
  modern: {
    primary: {
      start: '#f0f4ff',
      end: '#e0e7ff',
      hoverStart: '#e0e7ff',
      hoverEnd: '#c7d2fe',
      text: '#4338ca',
      textHover: '#312e81'
    },
    success: {
      start: '#f0fdf4',
      end: '#dcfce7',
      hoverStart: '#dcfce7',
      hoverEnd: '#bbf7d0',
      text: '#059669',
      textHover: '#047857'
    },
    warning: {
      start: '#fffbeb',
      end: '#fef3c7',
      hoverStart: '#fef3c7',
      hoverEnd: '#fed7aa',
      text: '#d97706',
      textHover: '#92400e'
    },
    info: {
      start: '#fdf4ff',
      end: '#fae8ff',
      hoverStart: '#fae8ff',
      hoverEnd: '#f3e8ff',
      text: '#7c3aed',
      textHover: '#5b21b6'
    }
  }
};

// 当前激活的主题
export const currentTheme = 'classic';

// 应用主题到CSS变量
export const applyTheme = (themeName = currentTheme) => {
  const theme = buttonThemes[themeName];
  if (!theme) return;

  const root = document.documentElement;
  
  // 设置CSS变量
  Object.entries(theme).forEach(([type, colors]) => {
    Object.entries(colors).forEach(([key, value]) => {
      const cssVar = `--${type}-color-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`;
      root.style.setProperty(cssVar, value);
    });
  });
};

// 获取当前主题配置
export const getCurrentTheme = () => buttonThemes[currentTheme];

// 主题切换函数
export const switchTheme = (themeName) => {
  if (buttonThemes[themeName]) {
    applyTheme(themeName);
    // 可以在这里保存到localStorage
    localStorage.setItem('buttonTheme', themeName);
  }
}; 