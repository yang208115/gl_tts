"""原神语音合成

原神角色语音BertVITS2模型V1版是人工智能语音合成模型。
基于深度学习技术，结合BERT语言理解与VITS语音合成技术，
实现自然流畅的语音输出。它根据文本输入生成与角色声音特征匹配的语音，
优化了语音自然度、情感表达和合成准确性，使角色语音贴近原角色特点，
为玩家带来真实愉悦的听觉享受。
"""

import tempfile
import requests
import json
from nonebot import on_command, get_bot

from nonebot.adapters import Bot, Message
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nekro_agent.adapters.onebot_v11.matchers.command import command_guard
from nonebot.adapters.onebot.v11 import MessageSegment

from pydantic import Field

from nekro_agent.services.plugin.base import NekroPlugin, ConfigBase, SandboxMethodType
from nekro_agent.services.plugin.manager import save_plugin_config
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.core import logger


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
        default="https://gsv2p.acgnai.top/infer_single",
        title="TTS API URL",
        description="TTS服务的基础URL。",
    )
    token: str = Field(
        default="None",
        title="token",
        description="<a href='https://tts.acgnai.top ' target='_blank'>点击请往token</a> tts.acgnai.top的token",
    )
    DEFAULT_MODEL: str = Field(
        default="原神-中文-芙宁娜_ZH",
        title="模型",
        description="默认模型名称",
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
    插件直接输出语音到聊群，无需在作任何操作，直接调用即可
    
    Args:
        content: 需要合成的文本内容

    Returns:
        None

    Raises:
        ValueError: 当输入参数不符合要求时
        RuntimeError: 当API调用失败时

    Example:
        gl_tts("你好")
    """

    data = {
    "model_name": config.DEFAULT_MODEL,
    "emotion": '默认',
    "version": "v4",
    "prompt_text_lang": "中文",
    "text": content,
    "text_lang": "中文",
    "top_k": 10,
    "top_p": 1,
    "temperature": 1,
    "text_split_method": "按标点符号切",
    "batch_size": 10,
    "batch_threshold": 0.75,
    "split_bucket": True,
    "speed_facter": 1,
    "fragment_interval": 0.3,
    "media_type": "wav",
    "parallel_infer": True,
    "repetition_penalty": 1.35,
    "seed": -1,
    "sample_steps": 16,
    "if_sr": False
    }
    headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {config.token}",
    "Content-Type": "application/json",
    }



    # 创建临时目录用于存储文件
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            response = requests.post(config.API_URL, headers=headers, json=data, timeout=100)
            logger.info("请求完成")
            logger.info(f"API响应内容:{response.json()}")
            response.raise_for_status()  # 检查请求是否成功


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

        await send_audio(_ctx.from_chat_key, audio_url)


@plugin.mount_cleanup_method()
async def clean_up():
    """清理插件资源"""
    logger.info("TTS Plugin Resources Cleaned Up")

async def send_audio(chat_key, file):
    pairs =chat_key.split("_")
    chat_type = pairs[0]
    chat_id = pairs[2]
    bot = get_bot()
    audio = MessageSegment.record(file=file)
    try:
        if chat_type == 'onebot_v11-group':
            await bot.send_group_msg(group_id=chat_id, message=audio)
        else:
            await bot.send_private_msg(user_id=chat_id, message=audio)
    except Exception as e:
        raise RuntimeError(f"出现未知问题: {e}")   


@on_command('gl_tts_set').handle()
async def gl_tts_set(matcher: Matcher, event: MessageEvent, bot: Bot, arg: Message = CommandArg()):
    username, cmd_content, chat_key, chat_type = await command_guard(event, bot, arg, matcher)
    try:
        print('model:',await save_plugin_config('yang208115.gl_tts',{"DEFAULT_MODEL":cmd_content}))
    except Exception as e:
        pass

@on_command('gl_tts_help').handle()
async def gl_tts_help(matcher: Matcher, event: MessageEvent, bot: Bot, arg: Message = CommandArg()):
    await matcher.finish(message="使用/gl_tts_set来设置模型\n具体用法:\n/gl_tts_set [模型名]\n/gl_tts_set 原神-中文-芙宁娜_ZH\n\n\
至于支持什么模型和获取token,请自行前往\nhttps://tts.acgnai.top/ 查询\n查询模型时版本请选择v4")
