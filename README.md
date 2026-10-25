# luoxiaohei Codex Pet

**3D luoxiaohei pet** — 一个在 Codex / ChatGPT Windows 桌面客户端中使用的本地宠物。

![三种形态预览](assets/forms.png)

黑猫 → 黑发小孩 → 白发小孩，**每种形态停留 10 秒，30 秒循环**。三种形态共用一个宠物条目，每种均包含九组动作和十六个视线方向。

## 下载与安装

从 [Releases](https://github.com/JRHU0048/luoxiaohei-codex-pet/releases) 下载 `luoxiaohei-codex-pet-v1.0.0.zip` 并解压。

1. 先运行桌面客户端并登录一次，然后**完全退出客户端，包括托盘后台进程**。
2. 在解压目录打开 PowerShell，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Install-Pet.ps1
```

3. 重新打开客户端，观察完整的 30 秒轮换。显示名称为 `luoxiaohei`，说明为 `3D luoxiaohei pet`。

可以先使用 `-WhatIf` 查看操作计划；自定义 Codex 目录可传 `-CodexHome '你的目录'`。安装前会校验图片 SHA256，并把原文件和设置备份到 Codex 目录内的 `pet-backups/luoxiaohei/`。程序只需在安装时运行，轮换不依赖后台脚本或定时任务。

## 为什么必须使用本地文件

本项目把三个完整图集封装为一个动态 WebP，利用图片自身的时间轴切换形态。测试时，云端宠物上传链路会把它转换成单帧 PNG，导致只剩黑猫。

Windows 安装脚本会选择 `custom:luoxiaohei`，并调整该宠物的本地迁移记录，防止客户端改读云端静态副本。这使用了客户端的内部状态结构，不是公开的同步开关；脚本要求客户端停止运行并先备份，遇到未知结构会停止。仅修改本地文件、再上传到云端，不能保证保留轮换。

## 已验证范围

- Windows 桌面包 `26.1013.4894`，v2 图集 `1536 × 2288`、8 列 × 11 行、每格 `192 × 208`。
- 三个完整图集帧，时长均为 `10000 ms`，无限循环；无损构建保留源图集像素。
- 重启后持续 70 秒核对本地选择与迁移状态，均通过；使用者确认实际浮动宠物三形态轮换正常。
- 轮换依赖图片播放时间轴；重载、休眠或重新打开时可能从黑猫重新开始，不提供绝对时钟调度。其他客户端版本、系统和网页端未验证。

## 从源图集构建与验证

需要 Python 3.11+。安装脚本不需要额外的 Python 库，优先使用 Codex 自带的 Python 运行时；构建和验证图片时才需要安装 `requirements.txt` 中的依赖。也可通过 `-PythonExecutable` 指定运行时。

```shell
python -m pip install -r requirements.txt
python scripts/validate_pet.py
python scripts/build_pet.py
python -m unittest discover -s tests -p "test_*.py"
```

测试覆盖可复现构建、安装备份、其他设置保留、重复安装和运行中客户端保护，使用临时测试目录，不会修改本机客户端配置。

`source-atlases/` 是最终批准的三个静态图集，`pet/luoxiaohei/` 是可安装的动态文件。构建脚本不调用生成服务或 API；支持 `--seconds` 和 `--output` 进行实验性构建，验证时传相同的 `--seconds`。发布版安装脚本仅接受 `checksums.json` 记录的官方10秒版本。

维护者提交更改后，可运行 `python scripts/make_release.py`，从精确的 Git 提交生成发布 ZIP，自动排除本地设置和缓存文件。

## 许可与来源

代码和文档采用 [MIT](LICENSE)。本项目是非官方同人项目；角色图片单独说明，详见 [ASSETS.md](ASSETS.md)。原始参考图片、账号配置、私人路径、诊断日志和客户端源码均不包含在仓库中。

## English

A locally installed 3D Codex desktop pet cycling through a black cat, a black-haired child, and a white-haired child every 10 seconds. Use the Windows installer with the desktop client fully closed. The animation is encoded in the WebP itself; the tested cloud upload path flattens it. Code/documentation: MIT. Character artwork: see `ASSETS.md`.
