# 原神语音合成插件

基于深度学习技术，结合 GPT-Sovits V2 语音合成技术的原神角色语音合成工具，可根据文本输入生成与角色声音特征匹配的语音。

## 插件介绍

本插件依托原神角色语音 GPT-Sovits V2 模型 ，实现自然流畅的语音输出，优化语音自然度、情感表达和合成准确性，使角色语音贴近原角色特点，为用户带来真实愉悦的听觉享受。

## 使用


### 配置参数

在插件配置文件中设置以下参数：

| 参数名称          | 默认值                     | 描述                       |
|-------------------|----------------------------|----------------------------|
| API_URL           | https://gsv.ai-lab.top/infer_single | TTS 服务的基础 URL       |
| token             | None                       | 秘钥                       |
| DEFAULT_MODEL     | 【原神】枫丹               | 默认模型名称               |
| DEFAULT_SPEAKER   | 芙宁娜                     | 默认发音人名称             |
| DEFAULT_emotion   | 开心_happy                 | 默认情感                   |

## 主要功能

将文本内容转换为语音，并返回音频字节数据。

## 实现机制

### 动态调整参数

在聊天中可以通过命令动态更改模型、发音人、情感等参数：

```plaintext
/gl_tts_set DEFAULT_emotion=<情感> DEFAULT_SPEAKER=<发音人> DEFAULT_MODEL=<模型>
```

例如：
```plaintext
/gl_tts_set DEFAULT_emotion=开心_happy DEFAULT_SPEAKER=胡桃 DEFAULT_MODEL=【原神】璃月
```

### 发送请求

1. 创建一个字典类型的 `data`，其中包含 API 请求所需的参数，例如访问令牌、模型名称、发音人名称、文本内容、情感等。
2. 使用 `requests.post()` 方法向 TTS API 发送 POST 请求，将 `data` 作为 JSON 数据发送。
3. 检查请求是否成功，如果成功，则解析响应内容。

### 下载音频文件

1. 从响应数据中获取音频文件的 URL。
2. 检查保存目录是否存在，如果不存在则创建目录。
3. 使用 `requests.get()` 方法向音频文件 URL 发送 GET 请求，以流的形式下载文件。
4. 将下载的文件数据写入到指定的保存路径。

## 资源清理

提供资源清理功能，使用 `@plugin.mount_cleanup_method()` 装饰器定义的 `clean_up` 方法可在需要时清理插件资源。

## wiki
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/yang208115/gl_tts)

## 许可证

本插件采用 GNU General Public License v2.0 许可证。
