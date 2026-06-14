# 法考每日督学 V1

## 项目用途

本系统用于整理用户上传的法考 App 学习截图，辅助记录每日学习进度。

系统原则：

- 截图是唯一入口。
- 用户仍然在自己的法考 App 里做题、听课、复盘。
- 本系统不做题库，不生成题目，不判断答案。
- 本系统不爬取 App 数据，不自动登录第三方 App。
- 人工只负责确认和修正截图内容，确认后才生成正式学习记录。

## 电脑启动方式

双击运行：

```text
start_fakao_supervisor.bat
```

启动窗口不要关闭。电脑本机访问：

```text
http://localhost:8501
```

手机访问需要使用电脑局域网 IPv4 地址，例如：

```text
http://192.168.110.7:8501
```

如果 8501 端口被占用，可以改用 8508。

## 手机上如何使用

1. 电脑先启动系统：

```text
start_fakao_supervisor.bat
```

2. 手机和电脑连接同一个 Wi-Fi。

3. 在电脑运行：

```text
show_local_ip.bat
```

4. 找到推荐地址，例如：

```text
http://192.168.110.7:8501
```

5. 手机浏览器打开这个地址。

注意：手机不能访问电脑自己的 `localhost`。手机要用电脑的局域网 IPv4 地址。

## 手机打不开怎么办

### 1. 手机不能访问 localhost

`localhost` 只代表当前设备自己。手机上的 `localhost` 不是电脑。

错误示例：

```text
http://localhost:8501
```

正确示例：

```text
http://192.168.110.7:8501
```

### 2. 确认电脑端服务正在运行

电脑必须先启动：

```text
start_fakao_supervisor.bat
```

并且启动窗口不能关闭。

### 3. 确认监听方式

运行：

```text
check_network_8501.bat
```

如果只看到 `127.0.0.1:8501`，说明只能电脑本机访问，手机访问不了。

如果看到 `0.0.0.0:8501`，说明 Streamlit 已经对局域网开放，下一步重点查 Windows 防火墙或 Wi-Fi 设备隔离。

如果没有任何 `8501` 监听，说明 Streamlit 没启动，请运行 `start_fakao_supervisor.bat`。

### 4. 确认电脑 IP 正确

运行：

```text
show_local_ip.bat
```

优先使用脚本推荐的地址，例如：

```text
http://192.168.110.7:8501
```

不要使用：

- `127.0.0.1`
- `169.254.x.x`
- VPN / VirtualBox / VMware / WSL / Docker / Tailscale 等虚拟网卡地址

### 5. 防火墙问题

如果电脑能打开：

```text
http://电脑IPv4:8501
```

但手机打不开，请右键管理员运行：

```text
allow_firewall_8501.bat
```

这个脚本会删除旧规则并重新创建 `Fakao Streamlit 8501` 入站规则。

### 6. Wi-Fi 隔离问题

如果还是打不开，可能是路由器开启了设备隔离、访客网络隔离，或者电脑/手机开了 VPN。

建议测试：

- 手机开热点
- 电脑连接手机热点
- 重新启动系统
- 重新查看电脑 IPv4
- 手机访问新的 `IPv4:8501`

如果热点可以打开，说明原 Wi-Fi 有设备隔离。

## 最终排查顺序

请按这个顺序排查：

1. 电脑能不能打开：

```text
http://localhost:8501
```

2. 电脑能不能打开：

```text
http://电脑IPv4:8501
```

3. 手机能不能打开：

```text
http://电脑IPv4:8501
```

4. 如果第 2 步失败：重启 `start_fakao_supervisor.bat`，或运行：

```text
restart_fakao_8501.bat
```

5. 如果第 2 步成功、第 3 步失败：右键管理员运行：

```text
allow_firewall_8501.bat
```

6. 如果防火墙后仍失败：用手机热点测试。

7. 如果热点成功：原 Wi-Fi 有设备隔离或访客网络隔离。

8. 如果热点也失败：检查电脑 VPN、手机 VPN、杀毒软件、防火墙策略。

辅助脚本：

```text
phone_test_steps.bat
```

它会按步骤显示电脑和手机分别应该测试哪个地址。

## 如何添加到手机桌面

### iPhone

1. 用 Safari 打开系统地址。
2. 点击底部分享按钮。
3. 选择“添加到主屏幕”。
4. 名称填写“法考每日督学”。
5. 点击“添加”。

### Android

1. 用 Chrome 打开系统地址。
2. 点击右上角菜单。
3. 选择“添加到主屏幕”。
4. 名称填写“法考每日督学”。
5. 点击“添加”。

说明：

- 这不是原生 App，而是网页快捷入口。
- 电脑必须保持运行，手机才能访问。
- 如果以后部署到云服务器，就可以不依赖家里电脑。

## 当前未做

- 登录
- 云部署
- AI / OCR
- 周报
- 导出
- 今日任务匹配
- 人工新增学习记录
# 手机访问本机 Streamlit 说明

## 第一次修复

1. 双击运行：

```text
fix_streamlit_lan_admin.bat
```

2. Windows 弹出管理员权限确认时，点击“是”。
3. 修复完成后，双击运行：

```text
start_streamlit_lan.bat
```

4. 电脑浏览器先测试：

```text
http://localhost:8501
```

5. 双击查看电脑局域网 IPv4 地址：

```text
show_local_ip.bat
```

6. 手机浏览器地址栏输入：

```text
http://电脑IPv4地址:8501
```

示例：

```text
http://192.168.100.101:8501
```

注意：不要输入 `ipv4:8501`，不要在百度搜索框输入，要在手机浏览器地址栏输入数字 IP 地址。

## 以后日常启动

日常只需要双击：

```text
start_streamlit_lan.bat
```

启动窗口不要关闭。关闭窗口后，手机和电脑浏览器都会无法访问。

## 手机打不开时的判断顺序

1. 电脑先打开：

```text
http://localhost:8501
```

2. 电脑再打开：

```text
http://电脑IPv4地址:8501
```

3. 手机再打开同一个地址：

```text
http://电脑IPv4地址:8501
```

如果第 1 步打不开，说明 Streamlit 没启动，请重新双击 `start_streamlit_lan.bat`。

如果第 1 步能打开，但第 2 步打不开，说明监听方式或端口有问题，请运行：

```text
check_streamlit_lan.bat
```

如果第 2 步电脑能打开，但第 3 步手机打不开，优先运行：

```text
fix_streamlit_lan_admin.bat
```

或：

```text
allow_firewall_8501.bat
```

这两个脚本会用管理员权限创建或重建下面这条 Windows 防火墙规则：

```text
netsh advfirewall firewall add rule name="Allow Streamlit 8501 LAN" dir=in action=allow protocol=TCP localport=8501 profile=any
```

规则名称是 `Allow Streamlit 8501 LAN`，端口是 TCP 8501，Profile 覆盖 Domain / Private / Public。

如果放行防火墙后仍然打不开，通常是以下原因：

- 手机和电脑不在同一个 Wi-Fi
- 手机开了 VPN
- 手机正在使用流量
- 使用了访客 Wi-Fi
- 路由器开启 AP 隔离 / 设备隔离
- 公司、酒店、学校网络禁止设备互访

最后可以用手机热点测试：

1. 手机开启热点。
2. 电脑连接手机热点。
3. 重新双击 `start_streamlit_lan.bat`。
4. 重新双击 `show_local_ip.bat`。
5. 手机访问新的 `http://电脑IPv4地址:8501`。

如果热点可以打开，说明原来的 Wi-Fi 有设备隔离，不是本工具问题。
