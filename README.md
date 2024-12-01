# Arduino 雷达扫描系统

北京大学“创新与快速原型研制”课程作业2：“GUI Arduino 控制台”。基于Arduino和Python的雷达扫描与可视化系统，实现实时距离测量和图形化显示。

## 功能特点

- 舵机控制的（接近）180 度扫描
- 超声波距离测量
- 实时数据可视化
- LED指示灯环显示
- 串口通信控制

## 硬件要求

- Arduino Uno/Nano
- SG90舵机
- HC-SR04超声波传感器
- WS2812B LED灯环
- 连接线材

## 软件依赖

- Python 3.8+
- pyserial
- tkinter

## 快速开始

1. 安装依赖：
```bash
pip install -e .
```
2. 硬件连接：
- 舵机信号线 -> D9
- 超声波TRIG -> D6
- 超声波ECHO -> D7
- LED信号线 -> D8
3. 运行程序：
```bash
python radar_new.py
```
## 使用说明
通过串口向 Arduino 发送字符串，来实现功能：
- `START`：开始连续扫描
- `STOP`：停止扫描
- `ONCE`：单次扫描
- `LON/LOFF`：控制LED开关
- `A[angle]`：设置指定角度

## 许可证
MIT License