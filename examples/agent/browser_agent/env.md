# Windows 安装步骤

## 前置条件
- 安装 Python 3.10 或更高版本
- 安装 Node.js（用于 playwright）
- 安装 Chrome 浏览器
- 选择以下任一工具：
  - Conda（推荐 Anaconda 或 Miniconda）
  - 或 uv（Python 包管理工具）

## 安装步骤

### 1. 克隆项目仓库
```bash
git clone https://github.com/fresh-little-lemon/agentscope-private.git
cd agentscope-private
```

### 方式 A: 使用 Conda 安装

#### 2. 创建 Conda 虚拟环境
```bash
conda create -n agentscope python=3.12 -y
conda activate agentscope
pip install agentscope[full]
npx playwright install ffmpeg
```

### 方式 B: 使用 uv 安装

#### 2. 创建虚拟环境并安装依赖
```bash
uv venv --python 3.12 .venv
.venv\Scripts\activate
uv pip install agentscope[full]
npx playwright install ffmpeg
```

---

> **注意**: Windows 平台必须执行 `npx playwright install ffmpeg` 命令安装 FFmpeg


# Ubuntu 服务器安装步骤

## 前置条件
- 安装 Python 3.10 或更高版本
- 安装 Node.js（用于 playwright）
- 安装 Conda（推荐 Anaconda 或 Miniconda）
- 如果服务器无图形环境，使用 `npx playwright install` 安装 Chromium 浏览器

## 安装步骤
### 1. 克隆项目仓库
```bash
git clone https://github.com/fresh-little-lemon/agentscope-private.git
cd agentscope-private
```

### 2. 创建 Conda 虚拟环境并安装依赖
```bash
conda create -n agentscope python=3.12 -y
conda activate agentscope
pip install agentscope[full]
npx playwright install
```

> **注意**: 如果服务器无图形环境，`npx playwright install` 将自动安装 Chromium 浏览器。

## 启动 VLLM 服务（Qwen3-VL 模型）
### 1. 激活 VLLM 环境
```bash
conda activate evocua-vllm
```

### 2. 启动 VLLM 服务
```bash
CUDA_VISIBLE_DEVICES=1,2,4,5 vllm serve /home/gsy/models/Qwen/Qwen3-VL-32B-Instruct/ \
  --served-model-name qwen3-vl \
  --host 0.0.0.0 \
  --port 8081 \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 180000 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --enable-prompt-tokens-details
```
