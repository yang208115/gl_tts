"""原神语音合成

原神角色语音BertVITS2模型V1版是人工智能语音合成模型。
基于深度学习技术，结合BERT语言理解与VITS语音合成技术，
实现自然流畅的语音输出。它根据文本输入生成与角色声音特征匹配的语音，
优化了语音自然度、情感表达和合成准确性，使角色语音贴近原角色特点，
为玩家带来真实愉悦的听觉享受。
"""

import os
import tempfile
import requests
import json
import asyncio
from nonebot import on_command

from nonebot.adapters import Bot, Message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nekro_agent.matchers.command import command_guard, finish_with

from pydantic import BaseModel, Field

from nekro_agent.services.plugin.base import NekroPlugin, ConfigBase, SandboxMethodType
from nekro_agent.services.plugin.manager import save_plugin_config
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.core import logger

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

# 插件实例
plugin = NekroPlugin(
    name="原神语音合成插件",
    module_name="gl_tts",
    description="提供文本到语音合成功能",
    version="1.2.0",
    author="yang208115",
    url="https://github.com/yang208115/gl_tts",
)

# 定义可配置项
@plugin.mount_config()
class TTSConfig(ConfigBase):
    """语音合成配置"""
    API_URL: str = Field(
        default="https://gsv.ai-lab.top/infer_single",
        title="TTS API URL",
        description="TTS服务的基础URL。请前往https://gsv.acgnai.top/,获取token。",
    )
    token: str = Field(
        default="None",
        title="token",
        description="秘钥",
    )
    DEFAULT_MODEL: str = Field(
        default="【原神】枫丹",
        title="模型",
        description="默认模型名称",
    )
    DEFAULT_SPEAKER: str = Field(
        default="芙宁娜",
        title="发音人",
        description="默认发音人名称",
    )
    DEFAULT_emotion: str = Field(
        default="开心_happy",
        title="情感",
        description="情感",
    )
    
# 获取配置
config = plugin.get_config(TTSConfig)

@plugin.mount_sandbox_method(
    SandboxMethodType.TOOL,
    name="生成原神语音",
    description="将文本转换为语音并返回音频字节数据",
)
async def gl_tts(
    _ctx: AgentCtx,
    content: str,
) -> bytes:
    """文本转语音合成方法
    
    Args:
        content: 需要合成的文本内容

    Returns:
        bytes: 音频文件的字节数据（WAV格式）

    Raises:
        ValueError: 当输入参数不符合要求时
        RuntimeError: 当API调用失败时

    Example:
        gl_tts("你好")
    """

    data = {
    "access_token": config.token,
    "model_name": config.DEFAULT_MODEL,
    "speaker_name": config.DEFAULT_SPEAKER,
    "prompt_text_lang": "中文",
    "emotion": config.DEFAULT_emotion,
    "text": content,
    "text_lang": "中文",
    "top_k": 10,
    "top_p": 1,
    "temperature": 1,
    "text_split_method": "按标点符号切",
    "batch_size": 1,
    "batch_threshold": 0.75,
    "split_bucket": True,
    "speed_facter": 1,
    "fragment_interval": 0.3,
    "media_type": "wav",
    "parallel_infer": True,
    "repetition_penalty": 1.35,
    "seed": -1
    }


    # 创建临时目录用于存储文件
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            response = requests.post(config.API_URL, headers=headers, json=data, timeout=10)
            response.raise_for_status()  # 检查请求是否成功

            logger.debug("API响应内容:")
            logger.debug(response.text)

            try:
                response_data = response.json()
                msg = response_data.get("msg")
                audio_url = response_data.get("audio_url")

                # 打印参数
                if msg:
                    logger.debug("消息:", msg)
                else:
                    logger.debug("未找到消息内容。")
                
                if audio_url:
                    logger.debug("音频链接:", audio_url)
                    await download_file(audio_url,tmpdir)
                else:
                    raise ValueError("未找到音频链接。")
            except json.JSONDecodeError:
                logger.error("API响应内容不是有效的JSON格式。")
                raise ValueError(f"API响应内容不是有效的JSON格式。{response.text}")
            except Exception as e:
                raise RuntimeError(f"出现未知问题: {e}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"请求失败: {e}。网络问题或API接口无法访问。请检查网页链接的合法性，确保网络连接正常，然后适当重试。")
        except Exception as e:
            raise RuntimeError(f"出现未知问题: {e}")


        # 读取音频文件
        with open(tmpdir+'/audio.wav', "rb") as f:
            audio_data = f.read()

            
        return audio_data


@plugin.mount_cleanup_method()
async def clean_up():
    """清理插件资源"""
    logger.info("TTS Plugin Resources Cleaned Up")


async def download_file(audio_url, save_dir):
    try:
        # 检查保存目录是否存在，如果不存在则创建
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 定义文件的完整路径（保存目录+文件名）
        file_path = os.path.join(save_dir, "audio.wav")

        logger.info(file_path)

        response = requests.get(audio_url, stream=True, timeout=10)
        response.raise_for_status()  # 检查请求是否成功

        # 保存音频文件到指定路径
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        logger.debug(f"音频文件已成功下载并保存为 {file_path}")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"下载失败: {e}。请检查音频链接的合法性或稍后再试。")
    except Exception as e:
        raise RuntimeError(f"出现未知问题: {e}")

@on_command('gl_tts_set').handle()
async def gl_tts_set(matcher: Matcher, event: MessageEvent, bot: Bot, arg: Message = CommandArg()):
    username, cmd_content, chat_key, chat_type = await command_guard(event, bot, arg, matcher)
    items = cmd_content.split()
    result_dict = {k:v for k,v in (item.split('=') for item in items)}
    json_str = json.dumps(result_dict, indent=4)
    parsed_json = json.loads(json_str)
    try:
        print('model:',await save_plugin_config('yang208115.gl_tts',{"DEFAULT_MODEL":parsed_json["DEFAULT_MODEL"]}))
    except Exception as e:
        pass
    try:
        print('speaker:',await save_plugin_config('yang208115.gl_tts',{"DEFAULT_SPEAKER":parsed_json["DEFAULT_SPEAKER"]}))
    except Exception as e:
        pass
    try:
        print('emotion:',await save_plugin_config('yang208115.gl_tts',{"DEFAULT_emotion":parsed_json["DEFAULT_emotion"]}))
    except Exception as e:
        pass

@on_command('gl_tts_get_model').handle()
async def gl_tts_set(matcher: Matcher, event: MessageEvent, bot: Bot, arg: Message = CommandArg()):
    url = "https://gsv.ai-lab.top/models"
    headers = {
        "accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    await finish_with(matcher, message=response.text)

@on_command('gl_tts_get_speaker').handle()
async def gl_tts_set(matcher: Matcher, event: MessageEvent, bot: Bot, arg: Message = CommandArg()):
    username, cmd_content, chat_key, chat_type = await command_guard(event, bot, arg, matcher)
    url = "https://gsv.ai-lab.top/spks"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "model": cmd_content
    }

    response = requests.post(url, json=data, headers=headers)

    try:
        data = json.loads(response.text)
        # 提取speakers部分并格式化
        speakers = data.get("speakers", {})
        formatted_speakers = ',\n'.join(
            f'"{name}": {json.dumps(speaker, ensure_ascii=False)}' for name, speaker in speakers.items()
        )
        # 构造最终的格式化字符串
        formatted_json = f'{{"msg": "获取成功", "speakers": {{\n{formatted_speakers}\n}}}}'
        await finish_with(matcher, message=formatted_json)
    except json.JSONDecodeError as e:
        print(f"JSON格式错误: {e}")