# 多端同步架构设计

## 一、业务需求与价值

### 1.1 核心场景

**用户旅程**
```
早上通勤 (手机小程序)
  └─ 学习机场场景对话 + 添加3个生词

中午休息 (Web浏览器)
  └─ 复习早上添加的生词

晚上回家 (iPad/桌面端)
  └─ 导出今日学习长图 + 查看学习报告
```

**痛点**
- ❌ 数据孤岛: 手机背的单词,电脑上看不到
- ❌ 重复学习: 不知道其他设备已完成的内容
- ❌ 进度丢失: 换设备后学习streak中断

**价值主张**
- ✅ 无缝切换: 任意设备继续学习
- ✅ 进度连续: 学习数据实时同步
- ✅ 跨设备协作: 手机收集 → 电脑整理

---

## 二、技术方案选型

### 2.1 方案对比

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **CloudBase实时数据库** | 零开发成本,自动同步 | 仅限微信生态,无法扩展Web | 纯小程序MVP |
| **轮询(Polling)** | 实现简单,兼容性好 | 延迟高,资源浪费 | 低频更新场景 |
| **长轮询(Long Polling)** | 实时性较好,兼容性好 | 服务器压力大 | 过渡方案 |
| **WebSocket** | 双向实时,高效 | 需维护连接,复杂度高 | 高实时性需求 |
| **Server-Sent Events(SSE)** | 单向推送,简单 | 仅服务端推送 | 通知类场景 |
| **增量同步+版本控制** | 节省带宽,离线友好 | 实现复杂 | 大数据量同步 |

### 2.2 推荐方案(分阶段)

**MVP阶段: CloudBase + 轮询**
```
小程序(主力) ←→ CloudBase实时数据库 ←→ Web端(轮询)
```

**Phase 2: WebSocket + 增量同步**
```
小程序 ←→ WebSocket Server ←→ Web端
            ↓
       增量同步队列
            ↓
       CloudBase数据库
```

---

## 三、数据同步模型

### 3.1 同步粒度

**实体级同步 (推荐)**
```
同步单元 = 独立的数据实体
- 用户资料 (user profile)
- 学习计划 (plan)
- 场景进度 (scenario_progress)
- 词汇记录 (vocab item)
- 学习会话 (study session)
```

**优势**
- 冲突少: 不同实体独立更新
- 粒度适中: 不会过大或过小
- 易于缓存: 可按实体缓存

### 3.2 版本控制策略

**Lamport时间戳 + Last-Write-Wins (LWW)**

```json
{
  "entity_type": "vocab",
  "entity_id": "vocab_user123_hello",
  "version": 15,
  "updated_at": "2025-10-03T20:30:15.123Z",
  "updated_by": "device_iphone",

  "data": {
    "word": "hello",
    "phonetic": "/həˈloʊ/",
    "srs_level": 3,
    "next_review_at": "2025-10-05T09:00:00Z"
  },

  "tombstone": false  // 软删除标记
}
```

**冲突解决规则**
```python
def resolve_conflict(local: Entity, remote: Entity) -> Entity:
    """LWW冲突解决"""
    # 规则1: 时间戳优先
    if local.updated_at > remote.updated_at:
        return local
    elif local.updated_at < remote.updated_at:
        return remote

    # 规则2: 时间戳相同,版本号优先
    if local.version > remote.version:
        return local
    elif local.version < remote.version:
        return remote

    # 规则3: 都相同,保留本地(实际极少发生)
    return local
```

### 3.3 特殊数据处理

**累加型数据 (CRDT - Conflict-free Replicated Data Type)**
```json
{
  "entity_type": "study_stats",
  "entity_id": "stats_user123_20251003",

  "data": {
    "total_minutes": {
      "type": "counter",
      "increments": [
        { "device": "iphone", "value": 20, "ts": "2025-10-03T10:00:00Z" },
        { "device": "web", "value": 15, "ts": "2025-10-03T14:00:00Z" }
      ],
      "computed": 35  // sum(increments)
    },

    "sentences_learned": {
      "type": "set",
      "adds": ["sent_001", "sent_002", "sent_003"],
      "removes": [],
      "computed": 3
    }
  }
}
```

**冲突解决: 操作合并**
```python
def merge_counters(local: Counter, remote: Counter) -> Counter:
    """累加型数据合并"""
    all_increments = local.increments + remote.increments
    # 去重(基于device+ts)
    unique_increments = deduplicate(all_increments, key=lambda i: f"{i.device}_{i.ts}")
    return Counter(
        increments=unique_increments,
        computed=sum(i.value for i in unique_increments)
    )
```

---

## 四、同步协议设计

### 4.1 增量同步流程

```
Client                            Server
  |                                  |
  |-- GET /sync/changes?since=v10 ->|
  |                                  |
  |<-- {changes:[...], latest:v15}--|
  |                                  |
  |-- POST /sync/push -------------->|
  |    {changes:[...], base:v10}    |
  |                                  |
  |<-- {conflicts:[...], ok:true}---|
  |                                  |
```

### 4.2 API设计

**`GET /sync/changes`**
```python
@router.get("/sync/changes")
async def get_changes(
    since_version: int = Query(...),
    entity_types: list[str] = Query(None),
    user: User = Depends(get_current_user)
) -> SyncChangesResponse:
    """获取增量变更"""
    changes = await sync_repo.get_changes(
        user_id=user.openid,
        since_version=since_version,
        entity_types=entity_types or ["vocab", "progress", "plan"]
    )

    return {
        "changes": [c.to_dict() for c in changes],
        "latest_version": await sync_repo.get_latest_version(user.openid),
        "has_more": len(changes) >= 100,  # 分页
        "server_time": datetime.now().isoformat()
    }
```

**响应示例**
```json
{
  "changes": [
    {
      "entity_type": "vocab",
      "entity_id": "vocab_user123_hello",
      "action": "update",
      "version": 12,
      "updated_at": "2025-10-03T20:30:15Z",
      "data": { "word": "hello", "srs_level": 3 }
    },
    {
      "entity_type": "progress",
      "entity_id": "progress_user123_airport",
      "action": "update",
      "version": 13,
      "updated_at": "2025-10-03T20:32:00Z",
      "data": { "readiness": 0.78 }
    },
    {
      "entity_type": "vocab",
      "entity_id": "vocab_user123_goodbye",
      "action": "delete",
      "version": 14,
      "updated_at": "2025-10-03T20:35:00Z",
      "tombstone": true
    }
  ],
  "latest_version": 15,
  "has_more": false,
  "server_time": "2025-10-03T20:40:00Z"
}
```

**`POST /sync/push`**
```python
@router.post("/sync/push")
async def push_changes(
    payload: SyncPushRequest,
    user: User = Depends(get_current_user)
) -> SyncPushResponse:
    """推送本地变更"""
    conflicts = []
    applied = []

    for change in payload.changes:
        # 获取服务端最新版本
        server_entity = await sync_repo.get_entity(
            change.entity_type,
            change.entity_id
        )

        # 检测冲突
        if server_entity and server_entity.version > change.base_version:
            conflicts.append({
                "entity_id": change.entity_id,
                "client_version": change.version,
                "server_version": server_entity.version,
                "server_data": server_entity.data
            })
            continue

        # 应用变更
        await sync_repo.apply_change(change, user.openid)
        applied.append(change.entity_id)

    return {
        "applied": applied,
        "conflicts": conflicts,
        "latest_version": await sync_repo.get_latest_version(user.openid)
    }
```

### 4.3 冲突解决流程

**客户端处理**
```typescript
class SyncManager {
  async push(): Promise<void> {
    const localChanges = await this.getLocalChanges();

    const response = await api.post('/sync/push', {
      changes: localChanges,
      base_version: this.lastSyncVersion
    });

    // 处理冲突
    if (response.conflicts.length > 0) {
      for (const conflict of response.conflicts) {
        const resolved = await this.resolveConflict(
          conflict.entity_id,
          conflict.server_data
        );

        // 使用服务端数据覆盖本地(LWW策略)
        await this.db.update(conflict.entity_id, resolved);
      }

      // 重新推送
      await this.push();
    }

    this.lastSyncVersion = response.latest_version;
  }

  async resolveConflict(entityId: string, serverData: any): Promise<any> {
    const localData = await this.db.get(entityId);

    // LWW: 比较时间戳
    if (new Date(localData.updated_at) > new Date(serverData.updated_at)) {
      return localData;  // 保留本地
    } else {
      return serverData;  // 使用服务端
    }
  }
}
```

---

## 五、客户端实现

### 5.1 小程序端(主动推送)

**同步管理器 (`services/sync-manager.ts`)**
```typescript
class MiniProgramSyncManager {
  private db: WxDatabase;
  private syncInterval: number = 30000; // 30秒
  private syncTimer: number | null = null;

  constructor() {
    this.db = wx.cloud.database();
    this.setupRealtimeListener();
  }

  // CloudBase实时监听
  private setupRealtimeListener() {
    const watcher = this.db.collection('sync_changes')
      .where({ user_id: this.getUserId() })
      .watch({
        onChange: (snapshot) => {
          this.handleRealtimeChanges(snapshot.docs);
        },
        onError: (err) => {
          console.error('Realtime sync error:', err);
          this.fallbackToPolling();
        }
      });
  }

  private fallbackToPolling() {
    if (this.syncTimer) return;

    this.syncTimer = setInterval(() => {
      this.pull();
    }, this.syncInterval);
  }

  // 拉取变更
  async pull(): Promise<void> {
    const lastVersion = this.getLastSyncVersion();

    const response = await request.get('/sync/changes', {
      params: { since_version: lastVersion }
    });

    for (const change of response.changes) {
      await this.applyChange(change);
    }

    this.setLastSyncVersion(response.latest_version);
    this.notifyUI('sync_completed');
  }

  // 推送变更
  async push(): Promise<void> {
    const pendingChanges = await this.getPendingChanges();

    if (pendingChanges.length === 0) return;

    const response = await request.post('/sync/push', {
      changes: pendingChanges,
      base_version: this.getLastSyncVersion()
    });

    // 处理冲突
    if (response.conflicts.length > 0) {
      await this.resolveConflicts(response.conflicts);
    }

    // 清除已同步的变更
    await this.clearSyncedChanges(response.applied);
  }

  // 应用变更到本地
  private async applyChange(change: SyncChange): Promise<void> {
    const collection = this.getCollectionName(change.entity_type);

    if (change.action === 'delete') {
      await this.db.collection(collection).doc(change.entity_id).remove();
    } else {
      await this.db.collection(collection).doc(change.entity_id).set({
        data: {
          ...change.data,
          _version: change.version,
          _synced: true
        }
      });
    }
  }

  // 获取待同步变更
  private async getPendingChanges(): Promise<SyncChange[]> {
    const collections = ['vocab', 'progress', 'plans'];
    const changes: SyncChange[] = [];

    for (const coll of collections) {
      const docs = await this.db.collection(coll)
        .where({ _synced: false })
        .get();

      for (const doc of docs.data) {
        changes.push({
          entity_type: coll,
          entity_id: doc._id,
          action: doc._deleted ? 'delete' : 'update',
          version: doc._version || 0,
          updated_at: doc.updated_at,
          data: doc
        });
      }
    }

    return changes;
  }

  // 主动同步触发点
  async syncNow(): Promise<void> {
    await this.push();
    await this.pull();
  }

  // 在关键操作后触发同步
  async onDataChanged(entityType: string, entityId: string): Promise<void> {
    // 标记为未同步
    await this.db.collection(entityType).doc(entityId).update({
      data: { _synced: false }
    });

    // 延迟同步(避免频繁请求)
    this.debouncedSync();
  }

  private debouncedSync = debounce(() => this.syncNow(), 3000);
}

// 导出单例
export const syncManager = new MiniProgramSyncManager();
```

**使用示例**
```typescript
// 在添加生词后触发同步
async function addVocab(word: string) {
  const db = wx.cloud.database();
  const result = await db.collection('vocab').add({
    data: {
      word,
      user_id: getUserId(),
      created_at: new Date().toISOString(),
      _synced: false,
      _version: 0
    }
  });

  // 触发同步
  await syncManager.onDataChanged('vocab', result._id);
}
```

### 5.2 Web端(轮询)

**同步管理器 (`src/services/sync.ts`)**
```typescript
class WebSyncManager {
  private lastSyncVersion: number = 0;
  private pollInterval: number = 5000; // 5秒轮询
  private pollTimer: number | null = null;
  private isOnline: boolean = true;

  constructor() {
    this.initializeSync();
    this.setupOnlineListener();
  }

  private async initializeSync() {
    // 从localStorage恢复版本号
    this.lastSyncVersion = parseInt(
      localStorage.getItem('last_sync_version') || '0'
    );

    // 立即同步一次
    await this.sync();

    // 启动轮询
    this.startPolling();
  }

  private setupOnlineListener() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.sync();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  private startPolling() {
    if (this.pollTimer) return;

    this.pollTimer = window.setInterval(() => {
      if (this.isOnline) {
        this.sync();
      }
    }, this.pollInterval);
  }

  private stopPolling() {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  async sync(): Promise<void> {
    try {
      // 拉取变更
      const response = await api.get('/sync/changes', {
        params: { since_version: this.lastSyncVersion }
      });

      if (response.changes.length > 0) {
        await this.applyChanges(response.changes);
        this.lastSyncVersion = response.latest_version;
        localStorage.setItem('last_sync_version', this.lastSyncVersion.toString());

        // 通知UI更新
        window.dispatchEvent(new CustomEvent('sync:updated', {
          detail: { changes: response.changes }
        }));
      }
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }

  private async applyChanges(changes: SyncChange[]): Promise<void> {
    const db = await this.getDB();

    for (const change of changes) {
      const store = db.transaction([change.entity_type], 'readwrite')
        .objectStore(change.entity_type);

      if (change.action === 'delete') {
        await store.delete(change.entity_id);
      } else {
        await store.put({
          id: change.entity_id,
          ...change.data,
          _version: change.version,
          _updated_at: change.updated_at
        });
      }
    }
  }

  private async getDB(): Promise<IDBDatabase> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('LangLearning', 1);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains('vocab')) {
          db.createObjectStore('vocab', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('progress')) {
          db.createObjectStore('progress', { keyPath: 'id' });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  // 页面可见性优化
  setupVisibilityOptimization() {
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // 页面不可见时降低轮询频率
        this.pollInterval = 30000; // 30秒
      } else {
        // 页面可见时恢复正常频率并立即同步
        this.pollInterval = 5000;
        this.sync();
      }

      this.stopPolling();
      this.startPolling();
    });
  }
}

export const syncManager = new WebSyncManager();
```

---

## 六、服务端实现

### 6.1 数据库设计

**新增集合: `sync_changes`**
```json
{
  "_id": "change_12345",
  "user_id": "openid_123",
  "entity_type": "vocab",
  "entity_id": "vocab_user123_hello",
  "action": "update",
  "version": 12,
  "updated_at": "2025-10-03T20:30:15.123Z",
  "updated_by": "device_iphone",

  "data": {
    "word": "hello",
    "phonetic": "/həˈloʊ/",
    "srs_level": 3,
    "next_review_at": "2025-10-05T09:00:00Z"
  },

  "tombstone": false,
  "synced_devices": ["device_iphone"],
  "created_at": "2025-10-03T20:30:15.123Z"
}
```

**索引**
```json
[
  {
    "collection": "sync_changes",
    "indexes": [
      { "keys": { "user_id": 1, "version": 1 } },
      { "keys": { "user_id": 1, "entity_type": 1, "entity_id": 1 }, "options": { "unique": true } },
      { "keys": { "created_at": 1 }, "options": { "expireAfterSeconds": 2592000 } }
    ]
  }
]
```

### 6.2 同步仓储实现

**`repositories/sync_repository.py`**
```python
class SyncRepository:
    def __init__(self, db_client: TCBClient):
        self.db = db_client

    async def get_changes(
        self,
        user_id: str,
        since_version: int,
        entity_types: list[str],
        limit: int = 100
    ) -> list[SyncChange]:
        """获取增量变更"""
        query = {
            "user_id": user_id,
            "version": {"$gt": since_version}
        }

        if entity_types:
            query["entity_type"] = {"$in": entity_types}

        docs = await self.db.query(
            collection="sync_changes",
            filter=query,
            sort={"version": 1},
            limit=limit
        )

        return [SyncChange.from_dict(doc) for doc in docs]

    async def apply_change(
        self,
        change: SyncChange,
        user_id: str
    ) -> int:
        """应用变更并生成新版本"""
        # 生成新版本号
        new_version = await self.get_next_version(user_id)

        # 更新实际数据
        await self._update_entity_data(change)

        # 记录同步变更
        await self.db.add(
            collection="sync_changes",
            document={
                "user_id": user_id,
                "entity_type": change.entity_type,
                "entity_id": change.entity_id,
                "action": change.action,
                "version": new_version,
                "updated_at": datetime.now().isoformat(),
                "updated_by": change.device_id,
                "data": change.data,
                "tombstone": change.action == "delete"
            }
        )

        return new_version

    async def get_next_version(self, user_id: str) -> int:
        """生成下一个版本号(单调递增)"""
        # 使用Redis INCR或数据库原子操作
        key = f"sync_version:{user_id}"
        return await redis.incr(key)

    async def get_latest_version(self, user_id: str) -> int:
        """获取最新版本号"""
        doc = await self.db.query(
            collection="sync_changes",
            filter={"user_id": user_id},
            sort={"version": -1},
            limit=1
        )
        return doc[0]["version"] if doc else 0

    async def _update_entity_data(self, change: SyncChange):
        """更新实际实体数据"""
        collection = change.entity_type

        if change.action == "delete":
            await self.db.delete(collection, change.entity_id)
        else:
            await self.db.update(
                collection,
                change.entity_id,
                {
                    **change.data,
                    "_version": change.version,
                    "updated_at": change.updated_at
                }
            )
```

---

## 七、性能优化

### 7.1 带宽优化

**差量压缩**
```python
def compress_changes(changes: list[SyncChange]) -> bytes:
    """使用gzip压缩变更数据"""
    import gzip
    import json

    data = json.dumps([c.to_dict() for c in changes])
    return gzip.compress(data.encode('utf-8'))
```

**字段过滤**
```typescript
// 只同步必要字段
interface MinimalVocabSync {
  word: string;
  srs_level: number;
  next_review_at: string;
  // 省略audio_url等大字段
}
```

### 7.2 缓存策略

**客户端缓存**
```typescript
class SyncCache {
  private cache = new Map<string, CachedEntity>();
  private maxAge = 300000; // 5分钟

  get(entityId: string): any | null {
    const cached = this.cache.get(entityId);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > this.maxAge) {
      this.cache.delete(entityId);
      return null;
    }

    return cached.data;
  }

  set(entityId: string, data: any) {
    this.cache.set(entityId, {
      data,
      timestamp: Date.now()
    });
  }
}
```

**服务端缓存**
```python
@cache(ttl=60)  # Redis缓存1分钟
async def get_user_sync_data(user_id: str) -> dict:
    """缓存用户同步数据"""
    return await sync_repo.get_all_data(user_id)
```

### 7.3 批量操作

**批量推送**
```typescript
class BatchSyncManager {
  private pendingChanges: SyncChange[] = [];
  private batchSize = 50;
  private flushTimer: number | null = null;

  addChange(change: SyncChange) {
    this.pendingChanges.push(change);

    if (this.pendingChanges.length >= this.batchSize) {
      this.flush();
    } else {
      this.scheduleFlush();
    }
  }

  private scheduleFlush() {
    if (this.flushTimer) return;

    this.flushTimer = setTimeout(() => {
      this.flush();
    }, 5000); // 5秒后批量提交
  }

  private async flush() {
    if (this.pendingChanges.length === 0) return;

    const batch = this.pendingChanges.splice(0);
    await api.post('/sync/push', { changes: batch });

    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
  }
}
```

---

## 八、离线支持

### 8.1 离线存储

**IndexedDB封装 (Web)**
```typescript
class OfflineStorage {
  private db: IDBDatabase;

  async saveForOffline(entityType: string, data: any[]) {
    const tx = this.db.transaction([entityType], 'readwrite');
    const store = tx.objectStore(entityType);

    for (const item of data) {
      await store.put(item);
    }
  }

  async getOfflineData(entityType: string): Promise<any[]> {
    const tx = this.db.transaction([entityType], 'readonly');
    const store = tx.objectStore(entityType);
    return await store.getAll();
  }
}
```

### 8.2 冲突队列

**离线操作队列**
```typescript
class OfflineQueue {
  private queue: PendingOperation[] = [];

  async enqueue(operation: PendingOperation) {
    this.queue.push(operation);
    await this.saveToStorage();
  }

  async processQueue() {
    while (this.queue.length > 0) {
      const op = this.queue[0];

      try {
        await this.executeOperation(op);
        this.queue.shift();
        await this.saveToStorage();
      } catch (error) {
        if (error.name === 'NetworkError') {
          break; // 网络错误,稍后重试
        } else {
          // 其他错误,移除该操作
          this.queue.shift();
          await this.logError(op, error);
        }
      }
    }
  }

  private async executeOperation(op: PendingOperation) {
    switch (op.type) {
      case 'add_vocab':
        await api.post('/vocab', op.data);
        break;
      case 'update_progress':
        await api.post('/study/progress', op.data);
        break;
    }
  }
}
```

---

## 九、安全与权限

### 9.1 数据隔离

```python
# 确保用户只能访问自己的数据
@router.get("/sync/changes")
async def get_changes(
    since_version: int,
    user: User = Depends(get_current_user)
):
    # 强制过滤user_id
    changes = await sync_repo.get_changes(
        user_id=user.openid,  # 从token获取,不接受客户端传参
        since_version=since_version
    )
    return changes
```

### 9.2 设备管理

**新增集合: `user_devices`**
```json
{
  "_id": "device_iphone_abc123",
  "user_id": "openid_123",
  "device_type": "ios",
  "device_name": "iPhone 13",
  "last_sync_at": "2025-10-03T20:30:00Z",
  "last_sync_version": 15,
  "registered_at": "2025-09-20T10:00:00Z"
}
```

---

## 十、监控与调试

### 10.1 同步日志

```python
@router.post("/sync/push")
async def push_changes(payload: SyncPushRequest, user: User):
    start_time = time.time()

    result = await sync_service.push_changes(payload, user.openid)

    # 记录同步日志
    await log_sync_event({
        "user_id": user.openid,
        "action": "push",
        "changes_count": len(payload.changes),
        "conflicts_count": len(result.conflicts),
        "duration_ms": (time.time() - start_time) * 1000,
        "timestamp": datetime.now().isoformat()
    })

    return result
```

### 10.2 同步状态UI

```xml
<view class="sync-status">
  <icon type="{{syncIcon}}" />
  <text class="sync-text">{{syncStatusText}}</text>
  <text class="last-sync">上次同步: {{lastSyncTime}}</text>

  <button wx:if="{{hasSyncError}}" bindtap="retrySync">
    重试同步
  </button>
</view>
```

---

## 十一、成本与排期

### 11.1 开发工作量

| 模块 | 预计时间 | 优先级 |
|------|----------|--------|
| 数据库设计(sync_changes) | 0.5天 | P0 |
| 服务端同步API | 2天 | P0 |
| 小程序同步管理器 | 2天 | P0 |
| Web端同步管理器 | 2天 | P1 |
| 冲突解决逻辑 | 1天 | P0 |
| 离线队列 | 1天 | P1 |
| 设备管理 | 1天 | P2 |
| 监控日志 | 0.5天 | P2 |

**MVP总计: 7天 (仅小程序+服务端)**
**完整版: 10天 (含Web端)**

### 11.2 运营成本

```
CloudBase实时数据库: ¥0 (包含在套餐内)
API调用(轮询): 约10万次/月 × ¥0.0001 = ¥10/月
数据传输: 约5GB/月 × ¥0.15 = ¥0.75/月
Redis(版本号): ¥30/月 (共享实例)

总计: ¥41/月
```

---

## 十二、验收标准

- [ ] 小程序添加生词,Web端5秒内可见
- [ ] 网络断开后操作,恢复后自动同步
- [ ] 多设备同时编辑,冲突正确解决
- [ ] 同步失败有明确错误提示
- [ ] 同步日志可查询分析

---

## 附录: 技术选型决策表

| 需求 | 方案A | 方案B | 最终选择 | 理由 |
|------|-------|-------|----------|------|
| 实时性 | WebSocket | 轮询 | **轮询(MVP)** | 实现简单,成本低 |
| 冲突解决 | OT | CRDT | **LWW** | 场景简单,无需复杂算法 |
| 离线支持 | ServiceWorker | IndexedDB | **IndexedDB** | 兼容性好,易调试 |
| 版本控制 | Lamport | Vector Clock | **Lamport** | 单调递增,易理解 |