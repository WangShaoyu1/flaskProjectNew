const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack'); // 引入 webpack

module.exports = {
    entry: './src/index.js',
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
            template: './public/index.html',
        }),
        // 新增：DefinePlugin 注入 process.env
        new webpack.DefinePlugin({
            'process.env': JSON.stringify({
                // 显式定义你需要的环境变量
                REACT_APP_API_URL: process.env.REACT_APP_API_URL || 'http://localhost:8081',
                NODE_ENV: process.env.NODE_ENV || 'development', // 可选
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
        open: true,
        historyApiFallback: true,
    },
    resolve: {
        extensions: ['.js', '.jsx'],
    },
};

