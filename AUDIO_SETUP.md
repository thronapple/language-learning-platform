# 音频资源配置指南

## 概述

语言学习平台的核心功能依赖音频资源。当前代码使用测试音频URL，生产环境需要替换为真实的语音资源。

## 当前状态

### 测试音频URL（需替换）

```javascript
// miniprogram/pages/study/study.js:29-30
const testAudioUrl = 'https://sample-videos.com/zip/10/mp3/mp3-16kbit/Kalimba.mp3'
```

⚠️ **此URL仅用于开发测试，不包含实际语音内容！**

## 音频资源方案

### 方案1：使用CloudBase对象存储（推荐）

#### 优势
- ✅ 集成CDN加速
- ✅ 统一管理
- ✅ 成本可控
- ✅ 自动备份

#### 配置步骤

1. **上传音频文件到CloudBase存储**

```bash
# 使用CloudBase CLI上传
cloudbase storage upload audio/sentence-001.mp3 /audio/sentence-001.mp3

# 批量上传
cloudbase storage upload audio/ /audio/ --recursive
```

2. **获取CDN URL**

- 登录CloudBase控制台
- 进入「存储」->「文件管理」
- 复制文件的CDN URL
- 格式示例：`https://xxx-xxx.tcb.qcloud.la/audio/sentence-001.mp3`

3. **在数据库中配置音频URL**

```javascript
// 添加内容时设置audio_url
{
  "id": "content-001",
  "type": "sentence",
  "text": "Hello, how are you?",
  "audio_url": "https://your-env.tcb.qcloud.la/audio/sentence-001.mp3",
  "segments": ["Hello,", "how are you?"],
  "segments_audio": [
    "https://your-env.tcb.qcloud.la/audio/segment-001-1.mp3",
    "https://your-env.tcb.qcloud.la/audio/segment-001-2.mp3"
  ]
}
```

#### 成本估算

- 存储：¥0.12/GB/月
- CDN流量：¥0.18/GB（国内）
- 1000个音频文件（@50KB）：约50MB → **¥0.01/月**
- 1000用户/月播放（@500MB）：**¥0.09/月**
- **月均成本：< ¥1**

### 方案2：第三方TTS服务

#### 推荐服务商

##### 1. 腾讯云语音合成（TTS）

- **定价**：免费额度5000次/月，超出¥0.002/次
- **接口**：[腾讯云TTS文档](https://cloud.tencent.com/document/product/1073)

集成示例：

```python
# backend/app/services/tts.py
from tencentcloud.tts.v20190823 import tts_client, models
from tencentcloud.common import credential

class TTSService:
    def __init__(self, secret_id: str, secret_key: str):
        cred = credential.Credential(secret_id, secret_key)
        self.client = tts_client.TtsClient(cred, "ap-guangzhou")

    def synthesize(self, text: str, lang: str = "zh_CN") -> bytes:
        """生成语音并返回音频数据"""
        req = models.TextToVoiceRequest()
        req.Text = text
        req.SessionId = uuid.uuid4().hex
        req.VoiceType = 1  # 女声
        req.Codec = "mp3"

        resp = self.client.TextToVoice(req)
        return base64.b64decode(resp.Audio)
```

##### 2. 百度AI语音合成

- **定价**：免费额度200万字/月
- **接口**：[百度TTS文档](https://ai.baidu.com/ai-doc/SPEECH/Qk38y8lrl)

##### 3. 讯飞语音合成

- **定价**：免费额度500万字/月
- **接口**：[讯飞TTS文档](https://www.xfyun.cn/doc/tts/online_tts/API.html)

#### 实现流程

```
1. 用户导入文本
   ↓
2. 后端调用TTS服务生成音频
   ↓
3. 上传音频到对象存储
   ↓
4. 保存CDN URL到数据库
   ↓
5. 前端播放音频
```

### 方案3：预录制音频库

#### 适用场景
- 标准化教学内容
- 专业录音需求
- 多语言/多方言

#### 推荐工具
- **录音软件**：Audacity（免费）、Adobe Audition（专业）
- **格式转换**：FFmpeg
- **批量处理**：Python + pydub

#### 音频规范

```yaml
格式: MP3
比特率: 64-128 kbps（语音）
采样率: 22050 Hz或44100 Hz
声道: 单声道（Mono）
文件命名: sentence-{id}.mp3, segment-{id}-{index}.mp3
```

批量转换示例：

```bash
# 使用FFmpeg批量转换
for file in audio/*.wav; do
  ffmpeg -i "$file" -codec:a libmp3lame -b:a 64k -ar 22050 -ac 1 \
    "${file%.wav}.mp3"
done
```

## 前端代码修改

### 移除测试音频URL

找到并修改以下文件：

**miniprogram/pages/study/study.js**

替换：

```javascript
// ❌ 删除测试URL
const testAudioUrl = 'https://sample-videos.com/zip/10/mp3/mp3-16kbit/Kalimba.mp3'
this.setData({ audioUrl: testAudioUrl })
```

改为：

```javascript
// ✅ 使用真实音频URL
this.setData({ audioUrl: (res && res.audio_url) || '' })

// 如果没有音频，显示提示
if (!this.data.audioUrl) {
  wx.showToast({
    title: '该内容暂无音频',
    icon: 'none'
  })
}
```

### 音频加载优化

```javascript
// 添加加载状态
data: {
  audioLoading: false,
  audioError: false
},

initAudio() {
  const audio = wx.createInnerAudioContext()

  audio.onWaiting(() => {
    this.setData({ audioLoading: true })
  })

  audio.onCanplay(() => {
    this.setData({ audioLoading: false })
  })

  audio.onError((err) => {
    console.error('音频加载失败:', err)
    this.setData({
      audioLoading: false,
      audioError: true
    })
    wx.showToast({
      title: '音频加载失败',
      icon: 'none'
    })
  })

  // 设置音频源
  if (this.data.audioUrl) {
    audio.src = this.data.audioUrl
  }

  this.setData({ audio })
}
```

## 数据库配置

### Content集合字段

```javascript
{
  "_id": "xxx",
  "id": "content-001",
  "type": "sentence",
  "text": "Hello, how are you?",
  "audio_url": "https://your-cdn.com/audio/sentence-001.mp3",  // 整体音频
  "segments": ["Hello,", "how are you?"],
  "segments_audio": [  // 分段音频（可选）
    "https://your-cdn.com/audio/segment-001-1.mp3",
    "https://your-cdn.com/audio/segment-001-2.mp3"
  ],
  "level": "A1",
  "tags": ["greeting", "conversation"]
}
```

### 批量导入音频URL

```python
# scripts/import_audio_urls.py
import json
from app.infra.tcb_client import TCBClient
from app.infra.config import settings

client = TCBClient.from_settings(settings)

# 音频映射表
audio_mapping = {
    "content-001": {
        "audio_url": "https://xxx.tcb.qcloud.la/audio/sentence-001.mp3",
        "segments_audio": [
            "https://xxx.tcb.qcloud.la/audio/segment-001-1.mp3",
            "https://xxx.tcb.qcloud.la/audio/segment-001-2.mp3"
        ]
    },
    # ...更多映射
}

# 批量更新
for content_id, audio_data in audio_mapping.items():
    doc = client.get_document("content", content_id)
    if doc:
        doc.update(audio_data)
        client.update_document("content", content_id, doc)
        print(f"✓ Updated {content_id}")
```

## 测试验证

### 1. 音频可访问性测试

```bash
# 测试音频URL是否可访问
curl -I https://your-cdn.com/audio/sentence-001.mp3

# 应返回 200 OK
HTTP/1.1 200 OK
Content-Type: audio/mpeg
Content-Length: 51200
```

### 2. 小程序端测试

```javascript
// 测试音频播放
wx.createInnerAudioContext().src = 'https://your-audio-url.mp3'
```

### 3. 性能测试

- 首次加载时间 < 2秒
- 播放流畅无卡顿
- 网络切换自动重连

## 常见问题

### 音频无法播放

**可能原因：**
1. URL不可访问（404）
2. HTTPS证书问题
3. CORS跨域限制
4. 音频格式不支持

**解决方案：**
```bash
# 1. 检查URL可访问性
curl -I <audio-url>

# 2. 确保使用HTTPS
# 微信小程序仅支持HTTPS

# 3. 配置CORS（CloudBase自动配置）
# 对象存储 -> 权限管理 -> 跨域访问CORS

# 4. 确认格式支持
# 小程序支持：MP3, AAC, WAV, M4A
```

### 音频加载慢

**优化方案：**
1. 启用CDN加速
2. 压缩音频文件（64kbps语音）
3. 使用流式传输
4. 预加载下一句音频

```javascript
// 预加载下一句
preloadNext() {
  const nextIndex = this.data.activeIndex + 1
  const segAudios = this.data.segmentsAudio || []
  if (segAudios[nextIndex]) {
    const preload = wx.createInnerAudioContext()
    preload.src = segAudios[nextIndex]
    preload.onCanplay(() => {
      preload.destroy()
    })
  }
}
```

## 成本优化建议

1. **按需生成**：仅为常用内容预生成音频
2. **缓存策略**：TTS结果缓存，避免重复生成
3. **格式优化**：语音使用64kbps足够清晰
4. **CDN缓存**：设置合理的缓存时间（30天）

## 后续扩展

### AI评分功能（预告）

未来可接入语音识别API进行跟读评分：

- 腾讯云ASR（语音识别）
- 科大讯飞评测SDK
- 百度语音评测

预留字段：

```javascript
{
  "pronunciation_score": 85,  // 发音分数
  "fluency_score": 90,        // 流畅度
  "completeness": 1.0,        // 完整度
  "words": [                  // 逐词评分
    {"word": "hello", "score": 90},
    {"word": "world", "score": 80}
  ]
}
```

## 相关文档

- [CloudBase对象存储](https://cloud.tencent.com/document/product/876/19376)
- [微信小程序音频组件](https://developers.weixin.qq.com/miniprogram/dev/api/media/audio/InnerAudioContext.html)
- [腾讯云TTS](https://cloud.tencent.com/document/product/1073)
- [FFmpeg音频处理](https://ffmpeg.org/documentation.html)
