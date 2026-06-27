# 户外策划

粘贴两步路线路 URL，系统打开真实浏览器授权窗口；用户扫码登录并手动完成平台验证码后，系统自动下载 KML/GPX，并基于真实轨迹生成户外策划。

## 核心功能

- 多层 URL 编码的两步路 `trackId` 解析。
- 打开独立 Chrome/Edge 授权窗口并保留两步路登录状态。
- 登录后自动进入 KML 下载流程，监听真实下载结果。
- 轨迹距离、爬升、海拔、难度和预计时长分析。
- 可选出行日期与出发地点；浏览器定位可辅助填写出发地。
- 天气、地图、搜索与大模型 API Key 保存在当前浏览器，后端不持久化。
- 日期或出发地缺失时仅生成轨迹分析，不捏造天气和交通信息。

## 本地运行

后端：

```bash
cd backend
pip install -r requirements.txt
python main.py
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000`，后端 API 文档位于 `http://localhost:8000/docs`。

轨迹授权依赖本机可见的 Chrome 或 Edge。Docker 容器没有桌面浏览器时仍可运行其他接口，但不能完成两步路授权下载；此时页面会返回明确提示。可通过环境变量 `TWO_BULU_BROWSER_PATH` 指定浏览器路径。

## 验证

```bash
make test
make lint
make build
```

## 两步路访问边界

项目不会识别、绕过或代替用户完成两步路验证码，也不会规避 WAF 或访问控制。线路二维码只用于打开线路，并不是授权凭证。只有浏览器真实产生 KML/GPX 文件后，状态才会变为“轨迹就绪”。
