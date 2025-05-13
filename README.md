# 语音合成插件介绍

本插件是基于 NekroAgent 开发的语音合成工具，依托原神角色语音 BertVITS2 模型 V1 版这一先进的人工智能语音合成模型，能够将输入的文本转换为自然流畅的语音。该模型基于深度学习技术，巧妙融合了 BERT 语言理解与 VITS 语音合成技术，可根据文本输入精准生成与原神角色声音特征高度匹配的语音。
在语音自然度、情感表达和合成准确性方面，此模型经过了精心优化，使得输出的语音能高度贴近原神角色的声音特点，为用户带来如同置身于原神世界般真实且愉悦的听觉享受。
## 插件核心信息
### 基本配置
- **名称**：语音合成插件
- **模块名**：gl_tts
- **描述**：提供文本到语音合成功能
- **版本**：1.0.0
- **作者**：运阳
- **仓库链接**：[https://github.com/yang208115/gl_tts](https://github.com/yang208115/gl_tts)

### 可配置参数
插件提供了一系列可配置参数，方便根据不同需求进行调整：
- **API_URL**：TTS 服务的基础 URL，默认为 `https://aiboycoder-hoyotts.ms.show/`。
- **TIMEOUT**：API 请求的超时时间（秒），默认为 30 秒。
- **KEEP_TMP_FILE**：调试用开关，用于决定是否保留临时文件，生产环境应保持关闭。
- **LOG_LEVEL**：日志级别，默认为 `INFO`。
- **HTTP_RETRY_COUNT**：HTTP 请求重试次数，默认为 3 次。
- **DEFAULT_SPEAKER**：默认发音人名称，默认为“莱依拉”。
- **DEFAULT_SDP_RATIO**：默认 SDP/混合比例（0 - 1），推荐值为 0.2。
- **DEFAULT_NOISE_SCALE**：默认噪声比例，推荐值为 0.6。
- **DEFAULT_NOISE_SCALE_W**：默认音素长度噪声比例，推荐值为 0.8。
- **DEFAULT_LENGTH_SCALE**：默认语速比例（1 为正常），越大越慢。

### 主要功能
插件的核心功能是文本转语音合成，通过 `generate_speech` 方法实现：
```python
@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="生成语音",
    description="将文本转换为语音并返回音频字节数据",
)
async def generate_speech(
    _ctx: AgentCtx,
    content: str,
    speaker: str = None,
    sdp_ratio: float = None,
    noise_scale: float = None,
    noise_scale_w: float = None,
    length_scale: float = None
) -> bytes:
    # 函数实现逻辑...
```
该方法接收文本内容、发音人名称、SDP 比例、噪声比例、音素长度噪声比例和语速比例等参数，对输入参数进行校验后，向 TTS API 发送请求，获取生成的音频文件字节数据。

### 资源清理
插件还提供了资源清理功能，使用 `@plugin.mount_cleanup_method()` 装饰器定义的 `clean_up` 方法可在需要时清理插件资源：
```python
@plugin.mount_cleanup_method()
async def clean_up():
    logger.info("TTS Plugin Resources Cleaned Up")
```

## 许可证
本插件采用 GNU General Public License v2.0 许可证。 
