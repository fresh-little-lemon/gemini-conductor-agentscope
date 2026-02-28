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

# 启动 VLLM 服务（Qwen3.5-122B-A10B-FP8）

## 1. 激活 Conda 环境

```bash
conda activate evocua-vllm
```

---

## 2. 启动 VLLM 服务

```bash
cd /home/gsy/workspace/model_server/qwen3_5_vllm
source .venv/bin/activate
conda deactivate

CUDA_VISIBLE_DEVICES=1,2,4,5 vllm serve /data/models/Qwen/Qwen3.5-122B-A10B-FP8 \
  --served-model-name qwen3.5-122b-a10b \
  --port 8001 \
  --tensor-parallel-size 4 \
  --max-model-len 262144 \
  --reasoning-parser qwen3 \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --enable-prompt-tokens-details
```

---

# Troubleshooting

## `ValueError: System message must be at the beginning`

<details>
<summary>错误日志</summary>

```bash
(APIServer pid=34222) INFO:     127.0.0.1:36662 - "POST /v1/chat/completions HTTP/1.1" 200 OK
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484] An error occurred in `transformers` while applying chat template
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484] Traceback (most recent call last):
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/renderers/hf.py", line 472, in safe_apply_chat_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     return tokenizer.apply_chat_template(
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/transformers/tokenization_utils_base.py", line 1667, in apply_chat_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     rendered_chat, generation_indices = render_jinja_template(
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]                                         ^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/transformers/utils/chat_template_utils.py", line 539, in render_jinja_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     rendered_chat = compiled_template.render(
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]                     ^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 1295, in render
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     self.environment.handle_exception()
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 942, in handle_exception
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     raise rewrite_traceback_stack(source=source)
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "<template>", line 85, in top-level template code
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/jinja2/sandbox.py", line 401, in call
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     return __context.call(__obj, *args, **kwargs)
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/transformers/utils/chat_template_utils.py", line 447, in raise_exception
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484]     raise jinja2.exceptions.TemplateError(message)
(APIServer pid=34222) ERROR 02-28 17:03:00 [hf.py:484] jinja2.exceptions.TemplateError: System message must be at the beginning.
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] Error in preprocessing prompt inputs
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] Traceback (most recent call last):
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/renderers/hf.py", line 472, in safe_apply_chat_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     return tokenizer.apply_chat_template(
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/transformers/tokenization_utils_base.py", line 1667, in apply_chat_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     rendered_chat, generation_indices = render_jinja_template(
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]                                         ^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/transformers/utils/chat_template_utils.py", line 539, in render_jinja_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     rendered_chat = compiled_template.render(
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]                     ^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 1295, in render
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     self.environment.handle_exception()
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 942, in handle_exception
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     raise rewrite_traceback_stack(source=source)
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "<template>", line 85, in top-level template code
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/jinja2/sandbox.py", line 401, in call
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     return __context.call(__obj, *args, **kwargs)
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/transformers/utils/chat_template_utils.py", line 447, in raise_exception
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     raise jinja2.exceptions.TemplateError(message)
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] jinja2.exceptions.TemplateError: System message must be at the beginning.
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] 
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] The above exception was the direct cause of the following exception:
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] 
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] Traceback (most recent call last):
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/entrypoints/openai/chat_completion/serving.py", line 295, in render_chat_request
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     conversation, engine_prompts = await self._preprocess_chat(
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/entrypoints/openai/engine/serving.py", line 995, in _preprocess_chat
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     (conversation,), (engine_prompt,) = await renderer.render_chat_async(
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/renderers/base.py", line 755, in render_chat_async
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     for conv, prompt in await asyncio.gather(*rendered):
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/renderers/hf.py", line 694, in render_messages_async
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     prompt_raw = safe_apply_chat_template(
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]                  ^^^^^^^^^^^^^^^^^^^^^^^^^
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]   File "/home/gsy/workspace/model_server/qwen3_5_vllm/.venv/lib/python3.12/site-packages/vllm/renderers/hf.py", line 487, in safe_apply_chat_template
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311]     raise ValueError(str(e)) from e
(APIServer pid=34222) ERROR 02-28 17:03:00 [serving.py:311] ValueError: System message must be at the beginning.
(APIServer pid=34222) INFO:     127.0.0.1:36662 - "POST /v1/chat/completions HTTP/1.1" 400 Bad Request
```

</details>

### 原因

qwen3.5系列模型的默认 `chat_template.jinja` 要求：

> `system` message 必须位于对话的第一条消息。

当请求中的 `system` message 不在首位时，模板会触发异常：

```python
raise_exception("System message must be at the beginning.")
```

---

### 解决方案

修改 `chat_template.jinja`，移除该限制，使 `system` message 与 `user` message 使用相同的渲染逻辑。

```diff
@@ -84,6 +84,7 @@
 {%- if message.role == "system" %}
-    {%- if not loop.first %}
-        {{- raise_exception('System message must be at the beginning.') }}
-    {%- endif %}
+    {{- '<|im_start|>' + message.role + '\n' + content + '<|im_end|>' + '\n' }}
 {%- elif message.role == "user" %}
     {{- '<|im_start|>' + message.role + '\n' + content + '<|im_end|>' + '\n' }}
```

修改后：

* 不再强制 `system` message 必须位于第一条
* `system` 与 `user` message 将统一按相同格式渲染