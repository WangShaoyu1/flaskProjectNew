const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = {
    entry: './src/index-v2.js',
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'bundle.js',
        clean: true,
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: ['@babel/preset-env', '@babel/preset-react'],
                    },
                },
            },
            {
                test: /\.css$/i,
                use: ['style-loader', 'css-loader'],
            },
        ],
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: './public/index-v2.html',
            title: '智能对话训练平台 v2.0'
        }),
        new webpack.DefinePlugin({
            'process.env': JSON.stringify({
                // v2版本API地址
                REACT_APP_API_URL: process.env.REACT_APP_API_URL || 'http://localhost:8001',
                REACT_APP_API_VERSION: 'v2',
                NODE_ENV: process.env.NODE_ENV || 'development',
            }),
        })
    ],
    devServer: {
        static: {
            directory: path.join(__dirname, 'public'),
        },
        compress: true,
        port: 3000,
        hot: true,
        open: false,
        historyApiFallback: true,
        client: {
            logging: 'info',
            overlay: {
                errors: true,
                warnings: false,
            },
            progress: true,
        },
        devMiddleware: {
            stats: {
                colors: true,
                hash: false,
                version: false,
                timings: true,
                assets: true,
                chunks: false,
                modules: false,
                reasons: false,
                children: false,
                source: false,
                errors: true,
                errorDetails: true,
                warnings: true,
                publicPath: false,
            },
        },
        setupMiddlewares: (middlewares, devServer) => {
            if (!devServer.setupMiddlewares._startupLogged) {
                console.log('\n' + '='.repeat(60));
                console.log('🎨 智能对话训练平台 - 前端开发服务器');
                console.log('='.repeat(60));
                console.log(`⏰ 启动时间: ${new Date().toLocaleString('zh-CN')}`);
                console.log('📋 服务信息:');
                console.log('   - 前端服务: http://localhost:3000');
                console.log('   - 热重载: 已启用');
                console.log('   - 压缩: 已启用');
                console.log('='.repeat(60));
                console.log('🎯 服务已启动，等待请求...');
                console.log('='.repeat(60));
                devServer.setupMiddlewares._startupLogged = true;
            }
            
            devServer.app.use((req, res, next) => {
                const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
                const method = req.method;
                const url = req.url;
                const userAgent = req.get('User-Agent') || '';
                
                const skipPaths = ['/sockjs-node', '/ws', '/hot-update', '.hot-update.', '__webpack_hmr'];
                const shouldSkip = skipPaths.some(path => url.includes(path));
                
                if (!shouldSkip) {
                    const colors = {
                        reset: '\x1b[0m',
                        bright: '\x1b[1m',
                        red: '\x1b[31m',
                        green: '\x1b[32m',
                        yellow: '\x1b[33m',
                        blue: '\x1b[34m',
                        magenta: '\x1b[35m',
                        cyan: '\x1b[36m',
                        gray: '\x1b[90m'
                    };
                    
                    const getMethodColor = (method) => {
                        const methodColors = {
                            'GET': colors.green,
                            'POST': colors.blue,
                            'PUT': colors.yellow,
                            'DELETE': colors.red,
                            'PATCH': colors.magenta
                        };
                        return methodColors[method] || colors.gray;
                    };
                    
                    const isBrowser = userAgent.includes('Mozilla') || userAgent.includes('Chrome') || userAgent.includes('Safari');
                    const clientType = isBrowser ? '🌐' : '📡';
                    
                    let displayUrl = url;
                    if (url.length > 50) {
                        displayUrl = url.substring(0, 47) + '...';
                    }
                    
                    console.log(
                        `${colors.gray}[${timestamp}]${colors.reset} ` +
                        `${getMethodColor(method)}${method.padEnd(6)}${colors.reset} ` +
                        `${colors.cyan}${displayUrl}${colors.reset} ` +
                        `${colors.gray}${clientType}${colors.reset}`
                    );
                }
                
                next();
            });
            
            return middlewares;
        },
        watchFiles: {
            paths: ['src/**/*', 'public/**/*'],
            options: {
                usePolling: false,
            },
        },
    },
    resolve: {
        extensions: ['.js', '.jsx'],
    },
    stats: {
        colors: true,
        hash: false,
        version: false,
        timings: true,
        assets: true,
        chunks: false,
        modules: false,
        reasons: false,
        children: false,
        source: false,
        errors: true,
        errorDetails: true,
        warnings: true,
        publicPath: false,
        progress: true,
    },
};

