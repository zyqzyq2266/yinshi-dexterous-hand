# RH56DFTP-2L 左手灵巧手视觉跟随

使用电脑摄像头识别操作者的左手，并通过 USB-RS485 实时控制因时
RH56DFTP-2L 左手灵巧手的六个自由度。

> 本项目用于学习、演示和基础人机交互验证。灵巧手会产生真实运动，首次
> 使用或更改标定参数时，请保持手指周围无障碍物，并从单根手指的小幅动作开始。

```mermaid
flowchart LR
    A[电脑摄像头] --> B[MediaPipe HandLandmarker]
    B --> C[21 个手部关键点]
    C --> D[六轴手势映射]
    D --> E[限幅 死区 频率过滤]
    E --> F[USB-RS485]
    F --> G[RH56DFTP-2L 左手]
```

## 功能

- 实时读取摄像头，并在画面中显示手部关键点和六轴目标值。
- 识别镜像画面中的物理左手。
- 分别跟随小拇指、无名指、中指和食指的弯曲动作。
- 使用大拇指关节夹角控制弯曲轴；将旋转轴固定在标定值，避免横向外摆。
- 通过行程限幅、死区和发送频率限制，降低抖动和误动作风险。
- 提供 `--no-serial` 摄像头预览模式，以及 Windows 双击启动脚本。

## 硬件要求

| 项目 | 要求 |
| --- | --- |
| 灵巧手 | 因时 RH56DFTP-2L 左手 |
| 电源 | 灵巧手独立 24V 电源 |
| 通信 | USB-RS485 转接器 |
| 摄像头 | Windows 可用的普通 USB 摄像头或内置摄像头 |
| 软件 | Windows 10/11、Python 3.9 或更高版本 |

本项目开发时使用的设备参数为 `COM3`、`115200`、手部 ID `1`。你的设备
可能不同，应在本地 `config.yaml` 中修改，**不要提交该文件**。

## 从零部署

### 1. 获取代码

```powershell
git clone https://github.com/zyqzyq2266/yinshi-dexterous-hand.git
cd yinshi-dexterous-hand
```

也可以直接在 GitHub 页面点击 `Code` -> `Download ZIP`，解压后进入项目目录。

### 2. 创建 Python 环境并安装依赖

请先从 [Python 官网](https://www.python.org/downloads/windows/) 安装 Python 3.9
或更高版本，并在安装界面勾选 `Add Python to PATH`。如果终端中 `py` 命令不可用，
关闭并重新打开 PowerShell 后使用 `python` 替代下面命令中的 `py`。

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

如果电脑安装了多个 Python 版本，可将第一行改为 `py -3.12 -m venv .venv`。

### 3. 创建本机配置

```powershell
Copy-Item config.example.yaml config.yaml
```

打开 `config.yaml`，至少确认以下三项：

```yaml
serial_port: COM3   # 按设备管理器显示的实际端口修改
baudrate: 115200
hand_id: 1
```

默认模板使用 `motion_scale: 0.2`，仅用于首次小幅调试。完成实际方向和行程
校准后，才可以逐步提高该值。

### 4. 先验证摄像头，不控制硬件

```powershell
.\.venv\Scripts\python.exe -m hand_tracking.app --config config.yaml --no-serial
```

窗口中应能看到镜像画面和黄色手部关键点。按 `Esc` 退出。

### 5. 连接并校准灵巧手

1. 给灵巧手接通 24V 电源，并连接 USB-RS485。
2. 关闭因时上位机。上位机与本程序不能同时占用同一个 COM 口。
3. 确认手指周围无障碍物。
4. 启动实机控制：

```powershell
.\.venv\Scripts\python.exe -m hand_tracking.app --config config.yaml
```

5. 先缓慢活动一根手指。若实际方向相反，在 `config.yaml` 的
   `invert_axes` 中将对应轴设为 `true`，退出并重新启动。
6. 按 `Esc` 关闭窗口并释放串口。空格会发送 `open_pose`，首次调试前不要依赖
   它作为安全姿态。

Windows 用户也可以直接双击 `启动灵巧手跟随.bat`，它等价于第 5 步的命令。

## 项目结构

```text
yinshi-dexterous-hand/
├─ assets/hand_landmarker.task     # MediaPipe 手部识别模型
├─ hand_tracking/
│  ├─ app.py                       # 摄像头循环、窗口与程序入口
│  ├─ config.py                    # 配置读取和校验
│  ├─ mapper.py                    # 21 个关键点到六轴控制值的映射
│  ├─ rh56.py                      # RH56 串口协议
│  └─ safety.py                    # 限幅、死区和发送频率保护
├─ tests/                          # 自动化测试
├─ docs/PROJECT_REPORT.md          # 完整项目报告
├─ config.example.yaml             # 安全配置模板
├─ pyproject.toml                  # Python 依赖定义
└─ 启动灵巧手跟随.bat              # Windows 双击启动脚本
```

## 关键实现与标定过程

### 镜像左手识别

程序会镜像摄像头画面，便于操作者像照镜子一样活动左手。MediaPipe 在这种画面中
可能将物理左手标记为 `Right`，因此程序专门接受 `Right` 标签作为控制输入。

### 四指映射

四个手指各使用两个关节的夹角平均值计算弯曲量。硬件标定发现前四轴与视觉数值
方向相反，因此实际设备配置中使用前四轴反向。为使完整握拳达到足够行程，弯曲
增益设为 `13`，同时仍限制在 `0` 到 `1000`。

### 大拇指映射

直接使用大拇指在画面中的横向位置会误驱动旋转轴，使其外摆。当前方案将第六轴
固定为已标定值 `1000`，并通过大拇指 MCP-IP-指尖的关节夹角控制第五轴，从而
更适合张开和握拳时向掌心收拢的动作。

## 常见问题

| 现象 | 排查与解决 |
| --- | --- |
| 提示无法打开 COM 口 | 关闭因时上位机和其他串口工具，确认 `config.yaml` 中的端口正确。 |
| 摄像头黑屏 | 关闭占用摄像头的应用；尝试使用 `--camera 1` 选择另一摄像头。 |
| 识别不到左手 | 保持手掌朝向摄像头、光线充足；本程序接受镜像画面中的 `Right` 标签。 |
| 手指动作方向相反 | 仅调整对应的 `invert_axes` 项；一次只改一个轴。 |
| 手指运动过小或过大 | 从 `motion_scale: 0.2` 开始，完成方向验证后再逐步调高。 |
| 大拇指横向外摆 | 检查第六轴是否保持固定标定值；不要重新绑定到画面横向坐标。 |

## 测试

运行全部自动化测试：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

当前测试覆盖配置读取、六轴映射、反向逻辑、大拇指关节映射、RH56 串口数据帧、
安全过滤、丢失手部暂停和串口启动不自动发运动命令等行为。

## 如何高质量地向 AI 提问

灵巧手调试属于软硬件联合问题。描述越具体，AI 越容易给出能验证的修改，而不是
猜测。建议一次只调整一个问题，并提供下面四类信息：

1. **硬件事实**：型号、左/右手、COM 口、波特率、手部 ID、是否独立供电。
2. **复现步骤**：例如“握拳时其余四指已闭合，但大拇指仍向外伸”。
3. **证据**：控制窗口截图、上位机六轴读数、10 至 30 秒演示视频或报错全文。
4. **期望结果**：例如“大拇指应随握拳向掌心收拢，第六轴不应横向变化”。

可直接使用以下提问模板：

```text
我在 Windows 上使用 RH56DFTP-2L 左手，USB-RS485 为 COM3，115200，ID 1。
现象：{说明一个可重复的动作问题}。
我期望：{说明正确姿态或动作}。
我已尝试：{列出已修改的配置或代码}。
证据：{附上截图、视频或完整报错}。
请先判断可能的映射轴和原因，再给出一次只改一个变量的测试方案。
```

## 演示效果

为保护现场人员隐私，当前公开仓库**不包含演示视频**。建议后续录制时只拍摄
灵巧手与控制窗口，不显示人脸、账号、聊天记录或本机路径；可将处理后的 GIF
放在 `docs/demo.gif`，然后在这里添加：

```markdown
![灵巧手跟随演示](docs/demo.gif)
```

## 项目文档

- [项目报告](docs/PROJECT_REPORT.md)：构建过程、问题、解决方法与最终成果。
- [代码](hand_tracking/)：可直接查看摄像头、映射、串口协议和安全模块实现。

## 许可证

本项目使用 [MIT License](LICENSE)。使用者需自行确认其灵巧手、驱动和第三方
软件的许可条款，并对实际硬件操作负责。
