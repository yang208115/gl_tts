"""原神语音合成

原神角色语音BertVITS2模型V1版是人工智能语音合成模型。
基于深度学习技术，结合BERT语言理解与VITS语音合成技术，
实现自然流畅的语音输出。它根据文本输入生成与角色声音特征匹配的语音，
优化了语音自然度、情感表达和合成准确性，使角色语音贴近原角色特点，
为玩家带来真实愉悦的听觉享受。
"""

import os
import tempfile
from typing import Dict, Any
httpx = dynamic_importer("httpx")
# from gradio_client import Client
gradio_client = dynamic_importer("gradio_client")
Client = gradio_client.Client
from pydantic import BaseModel, Field

from nekro_agent.services.plugin.base import NekroPlugin, ConfigBase, SandboxMethodType
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.core import logger

# 插件实例
plugin = NekroPlugin(
    name="语音合成插件",
    module_name="gl_tts",
    description="提供文本到语音合成功能",
    version="1.0.0",
    author="运阳",
    url="https://github.com/yang208115/gl_tts",
)

# 定义可配置项
@plugin.mount_config()
class TTSConfig(ConfigBase):
    """语音合成配置"""
    API_URL: str = Field(
        default="https://aiboycoder-hoyotts.ms.show/",
        title="TTS API URL",
        description="TTS服务的基础URL",
    )
    TIMEOUT: int = Field(
        default=30,
        title="API Timeout",
        description="API请求的超时时间(秒)",
    )
    KEEP_TMP_FILE: bool = Field(
        default=False,
        title="Keep Temporary File",
        description="调试用，生产环境应保持关闭",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        title="Log Level",
        description="日志级别",
    )
    HTTP_RETRY_COUNT: int = Field(
        default=3,
        title="HTTP Retry Count",
        description="HTTP请求重试次数",
    )
    DEFAULT_SPEAKER: str = Field(
        default="莱依拉",
        title="Default Speaker",
        description="默认发音人名称",
    )
    DEFAULT_SDP_RATIO: float = Field(
        default=0.2,
        title="Default SDP Ratio",
        description="默认SDP/混合比例（0-1）",
    )
    DEFAULT_NOISE_SCALE: float = Field(
        default=0.6,
        title="Default Noise Scale",
        description="默认噪声比例",
    )
    DEFAULT_NOISE_SCALE_W: float = Field(
        default=0.8,
        title="Default Noise Scale W",
        description="默认音素长度噪声比例",
    )
    DEFAULT_LENGTH_SCALE: float = Field(
        default=1,
        title="Default Length Scale",
        description="默认语速比例（1为正常）",
    )

# 获取配置
config = plugin.get_config(TTSConfig)

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
    """文本转语音合成方法
    
    Args:
        content: 需要合成的文本内容
        speaker: 发音人名称（如"莱依拉"）
        sdp_ratio: SDP/混合比例（0-1，推荐0.2）
        noise_scale: 噪声比例（推荐0.6）
        noise_scale_w: 音素长度噪声比例（推荐0.8）
        length_scale: 语速比例（1为正常，越大越慢）

    Returns:
        bytes: 音频文件的字节数据（WAV格式）

    Raises:
        ValueError: 当输入参数不符合要求时
        RuntimeError: 当API调用失败时

    Example:
        generate_speech("你好")
    """
    try:
        # 参数校验
        def validate_param(param, param_name, default_value, min_value=None, max_value=None):
            if param is None:
                return default_value
            if min_value is not None and param < min_value:
                raise ValueError(f"{param_name}不能小于{min_value}")
            if max_value is not None and param > max_value:
                raise ValueError(f"{param_name}不能大于{max_value}")
            return param

        speaker = validate_param(speaker, "speaker", config.DEFAULT_SPEAKER)
        sdp_ratio = validate_param(sdp_ratio, "sdp_ratio", config.DEFAULT_SDP_RATIO, 0, 1)
        noise_scale = validate_param(noise_scale, "noise_scale", config.DEFAULT_NOISE_SCALE, 0, 1)
        noise_scale_w = validate_param(noise_scale_w, "noise_scale_w", config.DEFAULT_NOISE_SCALE_W, 0, 1)
        length_scale = validate_param(length_scale, "length_scale", config.DEFAULT_LENGTH_SCALE, 0)

        # 设置日志级别
        logger.setLevel(config.LOG_LEVEL)

        # 创建临时目录用于存储文件
        with tempfile.TemporaryDirectory() as tmpdir:
            client = Client(config.API_URL, output_dir=tmpdir)
            
            # 向API发送请求
            result_path = await client.predict(
                content,
                speaker,
                sdp_ratio,
                noise_scale,
                noise_scale_w,
                length_scale,
                api_name="/predict"
            )
            
            # 读取音频文件
            with open(result_path, "rb") as f:
                audio_data = f.read()
            
            # 如果不需要保留临时文件，删除文件
            if not config.KEEP_TMP_FILE:
                os.remove(result_path)
            
            return audio_data

    except httpx.RequestError as e:
        logger.error(f"TTS Request Failed: {str(e)}")
        raise RuntimeError(f"TTS Service Connection Failed: {str(e)}") from e
    except httpx.HTTPStatusError as e:
        logger.error(f"TTS HTTP Error: {e.response.status_code}")
        raise RuntimeError(f"TTS Service Returned Error: {e.response.status_code}") from e
    except IOError as e:
        logger.error(f"File Operation Failed: {str(e)}")
        raise RuntimeError("Audio File Processing Failed") from e
    except ValueError as e:
        logger.error(f"Parameter Validation Failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unknown Error: {str(e)}")
        raise RuntimeError(f"TTS Failed: {str(e)}") from e

@plugin.mount_cleanup_method()
async def clean_up():
    """清理插件资源"""
    logger.info("TTS Plugin Resources Cleaned Up")
