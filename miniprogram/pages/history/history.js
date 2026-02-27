// pages/history/history.js
const app = getApp();

Page({
  data: {
    allList: [],
    filteredList: [],
    groupedList: [],
    filterType: 'all', // all, in, out
    stats: {
      todayIn: 0,
      todayOut: 0,
      totalIn: 0,
      totalOut: 0
    }
  },

  onShow() {
    this.loadHistory();
  },

  // 加载历史记录
  async loadHistory() {
    wx.showLoading({ title: '加载中...' });
    
    try {
      const res = await app.db.getHistory();
      const allList = (res.data || []).map(item => {
        return {
          ...item,
          timeStr: this.formatTime(item.time)
        };
      });
      
      this.setData({ allList });
      this.applyFilter();
      this.calculateStats(allList);
      
    } catch (err) {
      console.error('加载历史记录失败', err);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  // 设置筛选
  setFilter(e) {
    const type = e.currentTarget.dataset.type;
    this.setData({ filterType: type });
    this.applyFilter();
  },

  // 应用筛选
  applyFilter() {
    const { allList, filterType } = this.data;
    let filtered;
    
    if (filterType === 'all') {
      filtered = allList;
    } else {
      filtered = allList.filter(item => item.type === filterType);
    }
    
    // 按日期分组
    const grouped = this.groupByDate(filtered);
    
    this.setData({
      filteredList: filtered,
      groupedList: grouped
    });
  },

  // 按日期分组
  groupByDate(list) {
    const groups = {};
    const today = this.getDateString(new Date());
    const yesterday = this.getDateString(new Date(Date.now() - 86400000));
    
    list.forEach(item => {
      const dateStr = this.getDateString(new Date(item.time));
      let dateKey = dateStr;
      
      if (dateStr === today) {
        dateKey = '今天';
      } else if (dateStr === yesterday) {
        dateKey = '昨天';
      }
      
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(item);
    });
    
    // 转换为数组并按日期排序
    const result = Object.keys(groups).map(key => ({
      date: key,
      items: groups[key]
    }));
    
    return result;
  },

  // 计算统计数据
  calculateStats(list) {
    const today = this.getDateString(new Date());
    
    let todayIn = 0;
    let todayOut = 0;
    let totalIn = 0;
    let totalOut = 0;
    
    list.forEach(item => {
      const dateStr = this.getDateString(new Date(item.time));
      
      if (item.type === 'in') {
        totalIn += item.quantity;
        if (dateStr === today) {
          todayIn += item.quantity;
        }
      } else {
        totalOut += item.quantity;
        if (dateStr === today) {
          todayOut += item.quantity;
        }
      }
    });
    
    this.setData({
      stats: {
        todayIn,
        todayOut,
        totalIn,
        totalOut
      }
    });
  },

  // 格式化时间
  formatTime(date) {
    if (!date) return '';
    const d = new Date(date);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  },

  // 获取日期字符串
  getDateString(date) {
    const d = new Date(date);
    return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadHistory().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 删除单条历史记录
  async deleteRecord(e) {
    const id = e.currentTarget.dataset.id;
    
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条记录吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '删除中...' });
            await app.db.deleteHistory(id);
            wx.showToast({ title: '删除成功', icon: 'success' });
            this.loadHistory();
          } catch (err) {
            console.error('删除失败', err);
            wx.showToast({ title: '删除失败', icon: 'none' });
          } finally {
            wx.hideLoading();
          }
        }
      }
    });
  },

  // 清空所有历史记录
  async clearAllHistory() {
    wx.showModal({
      title: '清空历史',
      content: '确定要清空所有历史记录吗？此操作不可恢复！',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '清空中...' });
            await app.db.clearHistory();
            wx.showToast({ title: '已清空', icon: 'success' });
            this.loadHistory();
          } catch (err) {
            console.error('清空失败', err);
            wx.showToast({ title: '清空失败', icon: 'none' });
          } finally {
            wx.hideLoading();
          }
        }
      }
    });
  }
});
