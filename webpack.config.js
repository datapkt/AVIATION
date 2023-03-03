const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const TerserPlugin = require('terser-webpack-plugin');


module.exports = {
    entry: './src/js/app.js',
    mode: 'production',
    mode: 'development',
    output: {
      path: `${__dirname}/dist`,
      filename: 'bundle.js',
    },
    plugins: [new MiniCssExtractPlugin()],
    module: {
        rules: [
          {
            test: /\.css$/,
            use: [
              MiniCssExtractPlugin.loader,
              'css-loader',
            ],
          },
        ],
      },

      optimization: {
        minimize: true,
        minimizer: [
          new TerserPlugin({
          extractComments: false,
          }),
          new CssMinimizerPlugin(),
          //new OptimizeCssAssetsPlugin(),
        ],
        },
  };