"""
TTS (Text-to-Speech) 服务

支持多种TTS引擎:
- Google TTS (免费)
- Edge TTS (微软免费)
"""

import hashlib
import logging
from typing import Optional
from pathlib import Path
import urllib.parse

logger = logging.getLogger(__name__)


class TTSService:
    """文字转语音服务"""

    def __init__(self, storage_provider=None, cache_dir: str = "tts_cache"):
        """
        初始化TTS服务

        Args:
            storage_provider: 存储服务提供商 (用于保存生成的音频)
            cache_dir: 本地缓存目录
        """
        self.storage = storage_provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_key(self, text: str, lang: str, engine: str) -> str:
        """生成缓存键"""
        content = f"{text}_{lang}_{engine}"
        return hashlib.md5(content.encode()).hexdigest()

    def generate_google_tts_url(self, text: str, lang: str = "en") -> str:
        """
        生成Google TTS的URL (直接使用在线API)

        注意：微信小程序可能无法直接播放，需要后端代理

        Args:
            text: 要转换的文本
            lang: 语言代码 (en, zh-CN等)

        Returns:
            音频URL
        """
        # Google Translate TTS API (免费但有限制)
        base_url = "https://translate.google.com/translate_tts"
        params = {
            "ie": "UTF-8",
            "q": text,
            "tl": lang,
            "client": "tw-ob",
            "textlen": len(text)
        }
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"

    def download_tts_audio(self, text: str, lang: str = "en") -> Optional[str]:
        """
        下载TTS音频到本地缓存

        Args:
            text: 文本内容
            lang: 语言代码

        Returns:
            本地文件路径
        """
        try:
            import requests

            cache_key = self._get_cache_key(text, lang, "google")
            cache_file = self.cache_dir / f"{cache_key}.mp3"

            # 如果已缓存
            if cache_file.exists():
                logger.info(f"使用缓存的TTS音频: {cache_key}")
                return str(cache_file)

            # 下载音频
            url = self.generate_google_tts_url(text, lang)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # 保存到缓存
            cache_file.write_bytes(response.content)
            logger.info(f"下载并缓存TTS音频: {cache_key}")

            return str(cache_file)

        except ImportError:
            logger.warning("requests库未安装")
            return None
        except Exception as e:
            logger.error(f"下载TTS音频失败: {e}")
            return None

    async def generate_edge_tts_audio_async(self, text: str, voice: str = "en-US-JennyNeural") -> Optional[str]:
        """
        使用Edge TTS生成音频并返回本地文件路径（异步版本）

        Edge TTS 提供高质量、自然的语音，完全免费

        推荐语音:
        - en-US-JennyNeural: 美式英语女声，清晰友好（老师风格）
        - en-US-GuyNeural: 美式英语男声，专业稳重
        - en-GB-SoniaNeural: 英式英语女声，优雅专业
        - zh-CN-XiaoxiaoNeural: 中文女声

        Args:
            text: 要转换的文本
            voice: 语音名称

        Returns:
            本地音频文件路径
        """
        try:
            import edge_tts

            cache_key = self._get_cache_key(text, voice, "edge")
            cache_file = self.cache_dir / f"{cache_key}.mp3"

            # 如果已缓存，直接返回
            if cache_file.exists():
                logger.info(f"✅ [Edge TTS] 使用缓存音频 | 文本: '{text[:30]}...' | 语音: {voice} | 文件: {cache_key}")
                return str(cache_file)

            # 生成新音频（异步）
            logger.info(f"🎤 [Edge TTS] 开始生成音频 | 文本: '{text[:30]}...' | 语音: {voice}")

            # 可以设置速度和音调
            # rate: 语速 (-50% to +50%)，默认 +0%
            # pitch: 音调 (-50Hz to +50Hz)，默认 +0Hz
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate="+0%",  # 正常语速
                pitch="+0Hz"  # 正常音调
            )
            await communicate.save(str(cache_file))

            logger.info(f"✅ [Edge TTS] 音频生成成功 | 文件: {cache_key}.mp3 | 大小: {cache_file.stat().st_size} bytes")
            return str(cache_file)

        except ImportError:
            logger.warning("⚠️ [Edge TTS] edge-tts库未安装，无法使用Edge TTS")
            return None
        except Exception as e:
            logger.error(f"❌ [Edge TTS] 生成失败: {e}")
            return None

    async def get_tts_url_async(
        self,
        text: str,
        lang: str = "en",
        engine: str = "edge",
        voice: Optional[str] = None
    ) -> str:
        """
        获取TTS音频URL（异步版本）

        Args:
            text: 文本内容
            lang: 语言代码
            engine: TTS引擎 (edge, google)
            voice: 语音名称 (仅edge需要)

        Returns:
            音频文件路径或URL
        """
        logger.info(f"📢 [TTS] 请求生成 | 引擎: {engine} | 语言: {lang} | 文本: '{text[:50]}...'")

        # 优先使用Edge TTS（更自然的老师风格）
        if engine == "edge" or engine == "auto":
            voice = voice or self.get_voice_for_language(lang)
            audio_file = await self.generate_edge_tts_audio_async(text, voice)
            if audio_file:
                logger.info(f"✅ [TTS] 使用 Edge TTS 成功")
                return audio_file
            # 降级到Google TTS
            logger.warning("⚠️ [TTS] Edge TTS失败，降级到Google TTS")

        # 降级使用Google TTS
        logger.info(f"🔄 [TTS] 使用 Google TTS 降级方案")
        return self.download_tts_audio(text, lang) or self.generate_google_tts_url(text, lang)

    def get_voice_for_language(self, lang: str) -> str:
        """
        根据语言获取推荐的Edge TTS语音（老师风格）

        Args:
            lang: 语言代码

        Returns:
            语音名称
        """
        voice_map = {
            "en": "en-US-JennyNeural",  # 美式英语，清晰友好的老师风格
            "en-US": "en-US-JennyNeural",
            "en-GB": "en-GB-SoniaNeural",  # 英式英语，优雅专业
            "zh": "zh-CN-XiaoxiaoNeural",
            "zh-CN": "zh-CN-XiaoxiaoNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural"
        }
        return voice_map.get(lang, "en-US-JennyNeural")


# 简化的函数接口
def generate_tts_url(text: str, lang: str = "en", engine: str = "edge") -> str:
    """
    快速生成TTS URL（默认使用Edge TTS获得更自然的声音）

    Args:
        text: 文本内容
        lang: 语言代码
        engine: TTS引擎 (edge, google)

    Returns:
        音频文件路径或URL
    """
    service = TTSService()
    return service.get_tts_url(text, lang, engine)
