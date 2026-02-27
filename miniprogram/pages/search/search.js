// pages/search/search.js
const app = getApp();

Page({
  data: {
    keyword: '',
    resultList: [],
    hasSearched: false,
    searchHistory: []
  },

  onLoad() {
    this.loadSearchHistory();
  },

  // 加载搜索历史
  loadSearchHistory() {
    const history = wx.getStorageSync('searchHistory') || [];
    this.setData({ searchHistory: history });
  },

  // 输入框输入
  onInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  // 搜索
  async onSearch() {
    const keyword = this.data.keyword.trim();
    if (!keyword) {
      wx.showToast({ title: '请输入搜索关键词', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '搜索中...' });
    
    try {
      // 搜索货物
      const res = await app.db.searchGoods(keyword);
      const resultList = res.data || [];
      
      // 同时搜索位置匹配
      const allGoods = await app.db.getGoods();
      const locationMatch = (allGoods.data || []).filter(item => 
        item.location && item.location.includes(keyword)
      );
      
      // 合并结果并去重
      const combined = [...resultList];
      locationMatch.forEach(item => {
        if (!combined.find(g => g._id === item._id)) {
          combined.push(item);
        }
      });
      
      this.setData({
        resultList: combined,
        hasSearched: true
      });
      
      // 保存搜索历史
      this.saveSearchHistory(keyword);
      
    } catch (err) {
      console.error('搜索失败', err);
      wx.showToast({ title: '搜索失败', icon: 'none' });
    } finally {
      wx.hideLoading();
    }
  },

  // 保存搜索历史
  saveSearchHistory(keyword) {
    let history = wx.getStorageSync('searchHistory') || [];
    // 去除重复
    history = history.filter(item => item !== keyword);
    // 添加到开头
    history.unshift(keyword);
    // 限制最多10条
    history = history.slice(0, 10);
    wx.setStorageSync('searchHistory', history);
    this.setData({ searchHistory: history });
  },

  // 清除搜索历史
  clearHistory() {
    wx.showModal({
      title: '确认',
      content: '确定清除搜索历史？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('searchHistory');
          this.setData({ searchHistory: [] });
        }
      }
    });
  },

  // 从历史搜索
  searchFromHistory(e) {
    const keyword = e.currentTarget.dataset.keyword;
    this.setData({ keyword }, () => {
      this.onSearch();
    });
  },

  // 清除输入
  clearSearch() {
    this.setData({
      keyword: '',
      hasSearched: false,
      resultList: []
    });
  },

  // 查看货物详情
  viewGoods(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/operation/operation?goodsId=${id}`
    });
  }
});
