# 使用 Python 直接启动报价系统

本文说明如何绕过打包后的 EXE，直接从 Python 源码启动报价系统。以下命令均在 Windows PowerShell 中执行。

## 一、日常启动（推荐）

打开 PowerShell，进入项目根目录：

```powershell
cd "C:\Users\lfaf-test\Documents\报价系统\MechanicalQuotation"
```

启动桌面界面：

```powershell
.\.venv\Scripts\python.exe -m quotation.launcher --ui
```

`--ui` 可以省略，下面的命令效果相同：

```powershell
.\.venv\Scripts\python.exe -m quotation.launcher
```

启动本地 API 服务：

```powershell
.\.venv\Scripts\python.exe -m quotation.launcher --api
```

API 默认监听 `http://127.0.0.1:8000`，接口文档地址为 `http://127.0.0.1:8000/docs`。按 `Ctrl+C` 可停止 API。

## 二、首次运行

如果项目中还没有 `.venv`，请先在项目根目录创建虚拟环境并安装依赖。项目要求 Python 3.11 或更高版本。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

安装完成后，再执行日常启动命令。

## 三、不安装项目时临时启动

如果只想临时运行源码，可以把 `src` 加到本次 PowerShell 会话的模块搜索路径：

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m quotation.launcher --ui
```

这种方式只对当前 PowerShell 窗口有效，关闭窗口后设置自动失效。长期使用仍建议采用虚拟环境并执行 `pip install -e .`。

## 四、启动前检查

查看启动参数，且不真正打开界面：

```powershell
.\.venv\Scripts\python.exe -m quotation.launcher --help
```

执行系统自检：

```powershell
.\.venv\Scripts\python.exe -m quotation.launcher --self-check
```

## 五、常见问题

- 提示“找不到 `quotation` 模块”：确认当前目录是项目根目录，并执行 `.\.venv\Scripts\python.exe -m pip install -e .`。
- 提示找不到 `.venv\Scripts\python.exe`：虚拟环境尚未创建，请按“首次运行”操作。
- `py -3.11` 不可用：先安装 Python 3.11 或更高版本；也可根据本机版本改用 `py -3.12` 或 `python`。
- 8000 端口被占用：关闭已运行的 API/程序后重试。
- 桌面界面启动后命令窗口暂时不返回是正常现象；关闭界面后才会回到命令提示符。
