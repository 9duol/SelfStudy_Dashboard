# Dashboard Project

## 项目简介
该项目是一个全屏大屏幕看板，旨在实时显示当前时间、自习课纪律提醒以及实时噪音分贝数。该看板适用于学习环境，帮助学生保持专注并监控周围的噪音水平。

## 文件结构
```
dashboard-project
├── src
│   ├── main.py                # 应用程序入口点
│   ├── components
│   │   ├── clock.py           # 当前时间显示组件
│   │   ├── reminders.py        # 自习课纪律提醒组件
│   │   └── noise_meter.py      # 实时噪音分贝数组件
│   ├── utils
│   │   └── audio_processing.py  # 音频处理辅助函数
│   └── assets
│       └── styles.css          # 样式表
├── requirements.txt            # 项目依赖库
└── README.md                   # 项目文档
```

## 安装依赖
在项目根目录下，运行以下命令以安装所需的Python库：
```
pip install -r requirements.txt
```

## 使用说明
1. 确保已安装所有依赖项。
2. 运行 `src/main.py` 启动看板应用程序。
3. 看板将全屏显示当前时间、自习课纪律提醒和实时噪音分贝数。

## 贡献
欢迎任何形式的贡献！请提交问题或拉取请求以帮助改进该项目。

## 许可证
该项目采用MIT许可证。