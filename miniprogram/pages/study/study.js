const { request } = require('../../services/request')
const content = require('../../services/content')
const study = require('../../services/study')
const { track } = require('../../utils/track')

Page({
  data: {
    contentId: '',
    sentences: ['Hello world.', 'Nice to meet you.'],
    activeIndex: 0,
    activeAnchor: 'sentence-0',
    timer: null,
    secs: 0,
    autoNext: true,
    nextTimer: null,
    audio: null,
    audioUrl: '',
    isPlaying: false,
    audioRate: 1.0,
  },
  onLoad(options) {
    const id = options && options.id
    if (id) {
      content.get(id).then((res) => {
        const segs = (res && res.segments) || []
        const sentences = segs.length ? segs : [res.text || '']
        const segAudios = (res && res.segments_audio) || []
        // 音频URL - 优先使用真实音频，如果没有则显示提示
        const audioUrl = (res && res.audio_url) || ''
        const audioAvailable = !!audioUrl
        if (!audioAvailable) {
          console.warn('音频资源准备中，当前内容暂无音频')
        }
        this.setData({
          sentences,
          segmentsAudio: segAudios,
          activeIndex: 0,
          contentId: res.id || id,
          activeAnchor: 'sentence-0',
          audioUrl,
          audioAvailable
        })
        this.initAudio()
        this.startTimer()
        track('lesson_start', { contentId: res.id || id })
      })
    } else {
      // Fallback: fetch first content item
      content.list().then((res) => {
        const items = (res && res.items) || []
        if (items.length) {
          const first = items[0]
          return content.get(first.id).then((doc) => {
            const segs = (doc && doc.segments) || []
            const sentences = segs.length ? segs : [doc.text || '']
            const segAudios = (doc && doc.segments_audio) || []
            // 音频URL - 优先使用真实音频，如果没有则显示提示
            const audioUrl = (doc && doc.audio_url) || ''
            const audioAvailable = !!audioUrl
            if (!audioAvailable) {
              console.warn('音频资源准备中，当前内容暂无音频')
            }
            this.setData({
              sentences,
              segmentsAudio: segAudios,
              activeIndex: 0,
              contentId: doc.id || first.id,
              activeAnchor: 'sentence-0',
              audioUrl,
              audioAvailable
            })
            this.initAudio()
            this.startTimer()
            track('lesson_start', { contentId: doc.id || first.id })
          })
        } else {
          // 无内容时使用默认示例数据和测试音频
          const testAudioUrl = 'https://sample-videos.com/zip/10/mp3/mp3-16kbit/Kalimba.mp3'
          this.setData({ 
            sentences: ['Hello world.', 'Nice to meet you.'], 
            activeIndex: 0, 
            activeAnchor: 'sentence-0', 
            audioUrl: testAudioUrl 
          })
          this.initAudio()
          this.startTimer()
        }
      }).catch(() => {
        // 网络错误时使用默认示例数据
        const testAudioUrl = 'https://sample-videos.com/zip/10/mp3/mp3-16kbit/Kalimba.mp3'
        this.setData({ 
          sentences: ['Hello world.', 'Nice to meet you.'], 
          activeIndex: 0, 
          activeAnchor: 'sentence-0', 
          audioUrl: testAudioUrl 
        })
        this.initAudio()
        this.startTimer()
      })
    }
  },
  onUnload() {
    this.finish()
    // destroy audio
    if (this.data.audio) {
      try { this.data.audio.stop(); this.data.audio.destroy(); } catch (e) {}
      this.setData({ audio: null, isPlaying: false })
    }
  },
  initAudio() {
    if (this.data.audio) return
    const audio = wx.createInnerAudioContext()
    audio.autoplay = false
    
    // 音频事件监听
    audio.onEnded(() => {
      this.setData({ isPlaying: false })
      if (this.data.autoNext) this.next()
    })
    
    audio.onError((err) => {
      console.error('音频错误:', err)
      this.setData({ isPlaying: false })
      wx.showToast({ title: '音频加载失败', icon: 'none' })
    })
    
    audio.onCanplay(() => {
      console.log('音频可以播放')
    })
    
    // 设置初始音频源
    if (this.data.audioUrl) {
      audio.src = this.data.audioUrl
      console.log('设置音频源:', this.data.audioUrl)
    } else {
      console.log('未配置音频URL')
    }
    
    this.setData({ audio })
  },
  startTimer() {
    if (this.data.timer) return
    const t = setInterval(() => {
      this.setData({ secs: this.data.secs + 1 })
    }, 1000)
    this.setData({ timer: t })
  },
  stopTimer() {
    const t = this.data.timer
    if (t) {
      clearInterval(t)
      this.setData({ timer: null })
    }
  },
  setActive(i) {
    // 处理事件对象或直接传入的索引
    const index = typeof i === 'object' ? parseInt(i.currentTarget.dataset.index) : i
    const clamped = Math.max(0, Math.min(index, this.data.sentences.length - 1))
    this.setData({ activeIndex: clamped, activeAnchor: `sentence-${clamped}` })
    // switch audio per segment if available
    const segAudios = this.data.segmentsAudio || []
    if (segAudios.length && segAudios[clamped]) {
      const a = this.data.audio
      if (a) {
        try { a.src = segAudios[clamped]; if (this.data.isPlaying) a.play() } catch (e) {}
      }
    }
    if (this.data.autoNext) {
      if (this.data.nextTimer) clearTimeout(this.data.nextTimer)
      const nt = setTimeout(() => this.next(), 1500)
      this.setData({ nextTimer: nt })
    }
  },
  prev() {
    this.setActive(this.data.activeIndex - 1)
  },
  next() {
    const i = Math.min(this.data.sentences.length - 1, this.data.activeIndex + 1)
    this.setActive(i)
  },
  toggleAutoNext(e) {
    this.setData({ autoNext: e.detail.value })
  },
  togglePlay() {
    const a = this.data.audio
    if (!a) {
      wx.showToast({ title: '音频未加载', icon: 'none' })
      return
    }
    
    if (this.data.isPlaying) {
      try { 
        a.pause() 
        this.setData({ isPlaying: false })
      } catch (e) {
        console.error('音频暂停失败:', e)
        wx.showToast({ title: '暂停失败', icon: 'none' })
      }
    } else {
      if (!a.src) {
        wx.showToast({ title: '音频地址未配置', icon: 'none' })
        return
      }
      try { 
        a.play()
        this.setData({ isPlaying: true })
      } catch (e) {
        console.error('音频播放失败:', e)
        wx.showToast({ title: '播放失败，请检查网络', icon: 'none' })
        this.setData({ isPlaying: false })
      }
    }
  },
  cycleRate() {
    const rates = [1.0, 1.25, 1.5, 2.0]
    const cur = this.data.audioRate
    const idx = (rates.indexOf(cur) + 1) % rates.length
    const next = rates[idx]
    this.setData({ audioRate: next })
    const a = this.data.audio
    if (a && a.playbackRate) {
      try { a.playbackRate = next } catch (e) {}
    }
  },
  finish() {
    if (!this.data.contentId) return
    const secs = this.data.secs || 0
    // stop timers
    if (this.data.nextTimer) clearTimeout(this.data.nextTimer)
    this.stopTimer()
    // save progress
    study
      .saveProgress({ contentId: this.data.contentId, secs, step: 'learning' })
      .then(() => {
        track('lesson_finish', { contentId: this.data.contentId, secs })
        // try show finish interstitial (frequency controlled)
        try {
          const ad = this.selectComponent('#finishAd')
          if (ad && ad.maybeShow) ad.maybeShow()
        } catch (e) {}
      })
      .catch(() => {})
  },
})
