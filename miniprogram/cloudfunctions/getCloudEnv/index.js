// 云函数：获取云环境信息
const cloud = require('wx-server-sdk');
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

exports.main = async (event, context) => {
  return {
    env: cloud.DYNAMIC_CURRENT_ENV,
    message: '云环境配置成功'
  };
};
