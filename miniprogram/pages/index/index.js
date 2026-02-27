// pages/index/index.js
const app = getApp();

Page({
  data: {
    goodsList: [],
    recentHistory: [],
    stats: {
      total: 0,
      inStock: 0,
      lowStock: 0
    }
  },

  onShow() {
    this.loadData();
  },

  // 加载数据
  async loadData() {
    wx.showLoading({ title: '加载中...' });
    
    try {
      // 加载货物列表
      const goodsRes = await app.db.getGoods();
      const goodsList = goodsRes.data || [];
      
      // 计算统计数据
      const stats = {
        total: goodsList.length,
        inStock: goodsList.filter(g => g.stock > 10).length,
        lowStock: goodsList.filter(g => g.stock <= 10 && g.stock > 0).length
      };
      
      // 加载最近操作记录
      const historyRes = await app.db.getHistory();
      const historyList = (historyRes.data || []).slice(0, 5).map(item => {
        return {
          ...item,
          timeStr: this.formatTime(item.time)
        };
      });
      
      this.setData({
        goodsList,
        recentHistory: historyList,
        stats
      });
      
    } catch (err) {
      console.error('加载数据失败', err);
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    } finally {
      wx.hideLoading();
    }
  },

  // 格式化时间
  formatTime(date) {
    if (!date) return '';
    const d = new Date(date);
    const now = new Date();
    const diff = now - d;
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
    if (diff < 604800000) return Math.floor(diff / 86400000) + '天前';
    
    return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`;
  },

  // 查看货物详情
  viewGoods(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/operation/operation?goodsId=${id}`
    });
  },

  // 跳转到操作页面
  goToOperation() {
    wx.switchTab({
      url: '/pages/operation/operation'
    });
  },

  // 删除货物
  deleteGoods(e) {
    const id = e.currentTarget.dataset.id;
    const name = e.currentTarget.dataset.name;
    
    console.log('删除货物 - id:', id, 'name:', name);
    
    if (!id) {
      wx.showToast({
        title: '货物ID无效',
        icon: 'none'
      });
      return;
    }
    
    wx.showModal({
      title: '确认删除',
      content: `确定要删除货物"${name}"吗？`,
      confirmText: '删除',
      confirmColor: '#f5222d',
      success: (res) => {
        if (res.confirm) {
          this.doDeleteGoods(id);
        }
      }
    });
  },

  // 执行删除货物
  async doDeleteGoods(id) {
    wx.showLoading({ title: '删除中...' });
    
    try {
      console.log('执行删除 - id:', id);
      await app.db.deleteGoods(id);
      wx.showToast({
        title: '删除成功',
        icon: 'success'
      });
      // 重新加载数据
      this.loadData();
    } catch (err) {
      console.error('删除货物失败', err);
      wx.showToast({
        title: '删除失败: ' + (err.errMsg || err.message || '未知错误'),
        icon: 'none',
        duration: 3000
      });
    } finally {
      wx.hideLoading();
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh();
    });
  }
});
