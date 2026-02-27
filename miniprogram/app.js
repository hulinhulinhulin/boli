// app.js
const appInstance = {
  globalData: {
    // Flask 后端服务器地址
    // 开发环境：修改为你的电脑IP地址（局域网访问）
    // 例如：http://192.168.1.100:5000
    // 真机调试需要使用电脑的局域网IP
    serverUrl: 'http://192.168.1.13:5000'
  },

  // 封装 HTTP API 调用
  request(options) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: this.globalData.serverUrl + options.url,
        method: options.method || 'GET',
        data: options.data || {},
        header: options.header || { 'Content-Type': 'application/json' },
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else {
            reject(res.data || { errMsg: '请求失败' });
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  }
};

App({
  globalData: appInstance.globalData,

  onLaunch() {
    // 不再初始化云开发
    console.log('小程序启动，使用 Flask 后端 API');
  },

  // 封装云数据库操作 - 改为调用 HTTP API
  db: {
    // 获取所有货物
    getGoods() {
      return appInstance.request.call(this, {
        url: '/api/goods',
        method: 'GET'
      }).then(res => ({ data: res.goods || [] }));
    },

    // 添加货物
    addGoods(goods) {
      return appInstance.request.call(this, {
        url: '/api/goods',
        method: 'POST',
        data: goods
      });
    },

    // 更新货物（根据 _id）
    updateGoods(id, data) {
      return appInstance.request.call(this, {
        url: `/api/goods/by/_id/${id}`,
        method: 'PUT',
        data: data
      });
    },

    // 删除货物（根据 _id）
    deleteGoods(id) {
      return appInstance.request.call(this, {
        url: `/api/goods/by/_id/${id}`,
        method: 'DELETE'
      });
    },

    // 搜索货物
    searchGoods(keyword) {
      return appInstance.request.call(this, {
        url: '/api/goods/search?q=' + encodeURIComponent(keyword),
        method: 'GET'
      }).then(res => ({ data: res.goods || [] }));
    },

    // 获取操作历史
    getHistory() {
      return appInstance.request.call(this, {
        url: '/api/history',
        method: 'GET'
      }).then(res => ({ data: res.history || [] }));
    },

    // 添加历史记录
    addHistory(history) {
      return appInstance.request.call(this, {
        url: '/api/history',
        method: 'POST',
        data: history
      });
    },

    // 删除历史记录（根据 _id）
    deleteHistory(id) {
      return appInstance.request.call(this, {
        url: `/api/history/by/_id/${id}`,
        method: 'DELETE'
      });
    },

    // 清空所有历史记录
    clearHistory() {
      return appInstance.request.call(this, {
        url: '/api/history/clear',
        method: 'DELETE'
      });
    }
  }
});
