// pages/operation/operation.js
const app = getApp();

Page({
  data: {
    currentTab: 0, // 0: 取出, 1: 放入, 2: 新增货物
    goodsList: [],
    selectedGoodsIndex: -1,
    quantity: 1,
    isEditing: false,
    editGoodsId: '',
    
    // 新增货物表单
    newGoods: {
      name: '',
      location: '',
      price: '',
      stock: 0,
      description: ''
    }
  },

  onLoad(options) {
    this.loadGoodsList();
    
    // 如果传入了货物ID，说明是编辑模式
    if (options.goodsId) {
      this.setData({
        isEditing: true,
        editGoodsId: options.goodsId
      });
      this.loadGoodsDetail(options.goodsId);
    }
  },

  // 加载货物列表
  async loadGoodsList() {
    try {
      const res = await app.db.getGoods();
      this.setData({
        goodsList: res.data || []
      });
    } catch (err) {
      console.error('加载货物列表失败', err);
    }
  },

  // 加载货物详情
  async loadGoodsDetail(goodsId) {
    const goodsList = this.data.goodsList;
    const index = goodsList.findIndex(g => g._id === goodsId);
    if (index >= 0) {
      this.setData({
        selectedGoodsIndex: index,
        currentTab: 2, // 切换到编辑模式
        newGoods: {
          name: goodsList[index].name,
          location: goodsList[index].location,
          price: goodsList[index].price,
          stock: goodsList[index].stock,
          description: goodsList[index].description || ''
        }
      });
    }
  },

  // 切换Tab
  switchTab(e) {
    const index = parseInt(e.currentTarget.dataset.index);
    this.setData({
      currentTab: index,
      quantity: 1
    });
  },

  // 选择货物
  onGoodsSelect(e) {
    this.setData({
      selectedGoodsIndex: parseInt(e.detail.value)
    });
  },

  // 数量输入
  onInputQty(e) {
    let value = parseInt(e.detail.value) || 1;
    if (value < 1) value = 1;
    this.setData({ quantity: value });
  },

  // 增加数量
  increaseQty() {
    this.setData({
      quantity: this.data.quantity + 1
    });
  },

  // 减少数量
  decreaseQty() {
    if (this.data.quantity > 1) {
      this.setData({
        quantity: this.data.quantity - 1
      });
    }
  },

  // 新增货物表单输入
  onInputName(e) {
    this.setData({
      'newGoods.name': e.detail.value
    });
  },

  onInputLocation(e) {
    this.setData({
      'newGoods.location': e.detail.value
    });
  },

  onInputPrice(e) {
    this.setData({
      'newGoods.price': e.detail.value
    });
  },

  onInputStock(e) {
    this.setData({
      'newGoods.stock': parseInt(e.detail.value) || 0
    });
  },

  onInputDesc(e) {
    this.setData({
      'newGoods.description': e.detail.value
    });
  },

  // 提交操作
  async submitOperation() {
    const { currentTab, selectedGoodsIndex, goodsList, quantity, newGoods, isEditing, editGoodsId } = this.data;

    // 取出操作
    if (currentTab === 0) {
      if (selectedGoodsIndex < 0) {
        wx.showToast({ title: '请选择货物', icon: 'none' });
        return;
      }
      
      const goods = goodsList[selectedGoodsIndex];
      if (quantity > goods.stock) {
        wx.showToast({ title: '库存不足', icon: 'none' });
        return;
      }

      wx.showLoading({ title: '处理中...' });
      try {
        // 更新库存
        await app.db.updateGoods(goods._id, {
          stock: goods.stock - quantity
        });

        // 记录历史
        await app.db.addHistory({
          goodsId: goods._id,
          goodsName: goods.name,
          type: 'out',
          quantity: quantity,
          location: goods.location,
          price: goods.price
        });

        wx.showToast({ title: '取出成功', icon: 'success' });
        this.setData({ selectedGoodsIndex: -1, quantity: 1 });
        
      } catch (err) {
        console.error('取出失败', err);
        wx.showToast({ title: '操作失败', icon: 'none' });
      } finally {
        wx.hideLoading();
      }
    }

    // 放入操作
    if (currentTab === 1) {
      if (selectedGoodsIndex < 0) {
        wx.showToast({ title: '请选择货物', icon: 'none' });
        return;
      }

      const goods = goodsList[selectedGoodsIndex];
      
      wx.showLoading({ title: '处理中...' });
      try {
        // 更新库存
        await app.db.updateGoods(goods._id, {
          stock: goods.stock + quantity
        });

        // 记录历史
        await app.db.addHistory({
          goodsId: goods._id,
          goodsName: goods.name,
          type: 'in',
          quantity: quantity,
          location: goods.location,
          price: goods.price
        });

        wx.showToast({ title: '放入成功', icon: 'success' });
        this.setData({ selectedGoodsIndex: -1, quantity: 1 });
        
      } catch (err) {
        console.error('放入失败', err);
        wx.showToast({ title: '操作失败', icon: 'none' });
      } finally {
        wx.hideLoading();
      }
    }

    // 新增/编辑货物
    if (currentTab === 2) {
      if (!newGoods.name.trim()) {
        wx.showToast({ title: '请输入货物名称', icon: 'none' });
        return;
      }
      if (!newGoods.location.trim()) {
        wx.showToast({ title: '请输入存放位置', icon: 'none' });
        return;
      }
      if (!newGoods.price.trim()) {
        wx.showToast({ title: '请输入单价', icon: 'none' });
        return;
      }

      wx.showLoading({ title: '处理中...' });
      try {
        const goodsData = {
          name: newGoods.name.trim(),
          location: newGoods.location.trim(),
          price: parseFloat(newGoods.price),
          stock: newGoods.stock || 0,
          description: newGoods.description.trim(),
          createTime: new Date()
        };

        if (isEditing) {
          // 编辑模式
          await app.db.updateGoods(editGoodsId, goodsData);
          wx.showToast({ title: '更新成功', icon: 'success' });
        } else {
          // 新增模式
          await app.db.addGoods(goodsData);
          wx.showToast({ title: '添加成功', icon: 'success' });
        }

        // 重置表单
        this.setData({
          newGoods: {
            name: '',
            location: '',
            price: '',
            stock: 0,
            description: ''
          },
          isEditing: false,
          editGoodsId: ''
        });

      } catch (err) {
        console.error('操作失败', err);
        wx.showToast({ title: '操作失败', icon: 'none' });
      } finally {
        wx.hideLoading();
      }
    }
  },

  // 删除货物
  deleteGoods() {
    const { editGoodsId } = this.data;
    if (!editGoodsId) return;

    wx.showModal({
      title: '确认删除',
      content: '确定要删除这个货物吗？此操作不可恢复！',
      success: async (res) => {
        if (res.confirm) {
          wx.showLoading({ title: '删除中...' });
          try {
            await app.db.deleteGoods(editGoodsId);
            wx.showToast({ title: '删除成功', icon: 'success' });
            setTimeout(() => {
              wx.switchTab({ url: '/pages/index/index' });
            }, 1500);
          } catch (err) {
            console.error('删除失败', err);
            wx.showToast({ title: '删除失败', icon: 'none' });
          } finally {
            wx.hideLoading();
          }
        }
      }
    });
  }
});
