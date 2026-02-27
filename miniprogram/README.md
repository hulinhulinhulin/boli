# 仓库管理微信小程序

基于微信云开发的仓库管理系统，无需服务器，直接使用微信小程序即可运行。

## 功能特点

- 📦 货物管理：新增、编辑、删除货物
- 🔍 快速搜索：支持按名称和位置搜索
- 📥 库存操作：取出/放入货物，自动记录库存变化
- 📜 操作历史：完整记录所有进出库操作
- 📊 数据统计：实时统计库存状况

## 项目结构

```
miniprogram/
├── app.js              # 小程序入口
├── app.json            # 全局配置
├── app.wxss            # 全局样式
├── cloudfunctions/     # 云函数
│   └── getCloudEnv/   # 获取云环境
├── pages/
│   ├── index/         # 首页（货物列表）
│   ├── search/        # 搜索页面
│   ├── operation/     # 操作页面（取出/放入/新增）
│   └── history/       # 历史记录
└── project.config.json # 项目配置
```

## 使用步骤

### 1. 注册小程序账号
访问 [微信公众平台](https://mp.weixin.qq.com/) 注册小程序账号

### 2. 获取 AppID 和环境 ID
1. 登录小程序后台获取 AppID
2. 在微信开发者工具中创建云开发环境，获取环境 ID

### 3. 配置项目
1. 修改 `project.config.json` 中的 `appid` 为你的 AppID
2. 修改 `app.js` 中的 `cloudEnv` 为你的云环境 ID
3. 在微信开发者工具中上传并部署云函数：
   - 右键 `cloudfunctions/getCloudEnv` 文件夹
   - 选择 "上传并部署：云端安装依赖"

### 4. 创建数据库集合
在微信开发者工具的云开发控制台中创建以下集合：
- `goods` - 货物信息
- `history` - 操作历史

### 5. 运行项目
1. 用微信开发者工具打开 `miniprogram` 文件夹
2. 点击预览或真机调试

## 云数据库集合说明

### goods（货物集合）
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 货物名称 |
| location | string | 存放位置 |
| price | number | 单价 |
| stock | number | 库存数量 |
| description | string | 货物描述 |
| createTime | date | 创建时间 |

### history（历史记录集合）
| 字段 | 类型 | 说明 |
|------|------|------|
| goodsId | string | 货物ID |
| goodsName | string | 货物名称 |
| type | string | 操作类型 (in/out) |
| quantity | number | 操作数量 |
| location | string | 存放位置 |
| price | number | 单价 |
| time | date | 操作时间 |

## 截图预览

- 首页：显示货物列表和统计卡片
- 搜索：支持按名称和位置搜索
- 操作：取出/放入货物，新增货物
- 历史：查看所有操作记录

## 注意事项

1. 微信小程序需要使用已认证的 AppID 才能使用云开发
2. 云开发有免费配额，个人使用足够
3. 请确保在微信开发者工具中正确配置了云开发环境

## 技术栈

- 微信小程序原生开发
- 微信云开发（云数据库、云函数）
- CSS3 样式
