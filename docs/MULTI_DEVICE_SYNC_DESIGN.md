# 多设备同步实施方案

> **版本**: v1.0
> **创建日期**: 2025-12-29
> **状态**: 设计完成，待实施

---

## 目录

1. [概述](#概述)
2. [Phase 1: 基础 LWW 同步](#phase-1-基础-lww-同步)
3. [Phase 2: 增量同步协议](#phase-2-增量同步协议)
4. [Phase 3: 差异化合并策略](#phase-3-差异化合并策略)
5. [测试方案](#测试方案)
6. [部署检查清单](#部署检查清单)

---

## 概述

### 设计目标

- 支持用户在多个设备间无缝切换学习
- 支持 24 小时以上离线后的数据同步
- 最小化数据冲突和丢失
- 节省带宽（增量同步节省 90%+）

### 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 同步协议 | 增量 + 版本号 | 简单高效，适合低冲突场景 |
| 冲突策略 | 混合策略 | 按数据类型差异化处理 |
| 本地存储 | wx.storage | 小程序原生支持 |
| 版本追踪 | 全局递增版本号 | 实现简单，顺序明确 |

### 文件结构

```
backend/
├── app/
│   ├── domain/
│   │   └── sync.py              # 同步领域模型 (新增)
│   ├── services/
│   │   └── sync_service.py      # 同步服务 (新增)
│   ├── routes/
│   │   └── sync.py              # 同步API路由 (新增)
│   └── schemas/
│       └── sync.py              # 同步数据结构 (新增)

miniprogram/
├── services/
│   └── sync.ts                  # 同步服务 (新增)
├── utils/
│   └── storage.ts               # 本地存储封装 (新增)
└── store/
    └── sync-store.ts            # 同步状态管理 (新增)
```

---

## Phase 1: 基础 LWW 同步

> **目标**: 实现最简单的"最后写入获胜"同步
> **工作量**: 3-5 天

### 1.1 数据结构设计

#### 1.1.1 为现有集合添加同步字段

所有需要同步的集合添加以下字段：

```python
# backend/app/domain/sync.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class SyncMixin(BaseModel):
    """同步字段混入"""
    _version: int = Field(default=1, description="数据版本号")
    _updated_at: datetime = Field(default_factory=datetime.utcnow)
    _deleted: bool = Field(default=False, description="软删除标记")
    _device_id: Optional[str] = Field(default=None, description="最后修改设备")
```

#### 1.1.2 设备注册数据结构

```python
# backend/app/schemas/sync.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class DeviceType(str, Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"
    MINIPROGRAM = "miniprogram"

class DeviceInfo(BaseModel):
    """设备信息"""
    device_id: str
    device_type: DeviceType
    device_name: str
    device_model: Optional[str] = None
    app_version: str
    os_version: Optional[str] = None

class DeviceRegisterRequest(BaseModel):
    """设备注册请求"""
    device_info: DeviceInfo

class DeviceRegisterResponse(BaseModel):
    """设备注册响应"""
    device_id: str
    registered_at: datetime
    is_new_device: bool
    last_sync_version: int  # 该设备上次同步的版本号
```

#### 1.1.3 基础同步请求/响应

```python
# backend/app/schemas/sync.py (续)

class SyncType(str, Enum):
    FULL = "full"           # 全量同步
    INCREMENTAL = "incremental"  # 增量同步

class BasicSyncRequest(BaseModel):
    """基础同步请求 (Phase 1)"""
    device_id: str
    last_sync_at: Optional[datetime] = None  # 上次同步时间

class BasicSyncResponse(BaseModel):
    """基础同步响应 (Phase 1)"""
    sync_type: SyncType
    server_time: datetime
    data: dict  # 包含所有需要同步的数据
    # {
    #   "user_vocabulary": [...],
    #   "scenario_progress": [...],
    #   "learning_plans": [...],
    #   "users": {...}
    # }
```

### 1.2 后端实现

#### 1.2.1 同步服务

```python
# backend/app/services/sync_service.py

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from ..repositories.interfaces import Repository
from ..schemas.sync import (
    DeviceInfo, DeviceRegisterRequest, DeviceRegisterResponse,
    BasicSyncRequest, BasicSyncResponse, SyncType
)

class SyncService:
    """同步服务 - Phase 1: 基础LWW同步"""

    # 需要同步的集合列表
    SYNCABLE_COLLECTIONS = [
        "user_vocabulary",
        "scenario_progress",
        "learning_plans",
        "assessments"
    ]

    # 触发全量同步的条件
    FULL_SYNC_THRESHOLD_DAYS = 7

    def __init__(self, repo: Repository):
        self.repo = repo

    # ==================== 设备管理 ====================

    def register_device(
        self,
        user_id: str,
        request: DeviceRegisterRequest
    ) -> DeviceRegisterResponse:
        """注册设备"""
        device_id = request.device_info.device_id

        # 查找现有设备记录
        existing = self._find_device(user_id, device_id)

        if existing:
            # 更新设备信息
            existing.update({
                "device_name": request.device_info.device_name,
                "device_model": request.device_info.device_model,
                "app_version": request.device_info.app_version,
                "last_active_at": datetime.utcnow().isoformat(),
                "is_active": True
            })
            self.repo.put("user_devices", existing)

            return DeviceRegisterResponse(
                device_id=device_id,
                registered_at=datetime.fromisoformat(existing["registered_at"]),
                is_new_device=False,
                last_sync_version=existing.get("last_sync_version", 0)
            )

        # 创建新设备记录
        now = datetime.utcnow()
        device_doc = {
            "user_id": user_id,
            "device_id": device_id,
            "device_type": request.device_info.device_type.value,
            "device_name": request.device_info.device_name,
            "device_model": request.device_info.device_model,
            "app_version": request.device_info.app_version,
            "os_version": request.device_info.os_version,
            "registered_at": now.isoformat(),
            "last_active_at": now.isoformat(),
            "last_sync_at": None,
            "last_sync_version": 0,
            "is_active": True
        }
        self.repo.put("user_devices", device_doc)

        return DeviceRegisterResponse(
            device_id=device_id,
            registered_at=now,
            is_new_device=True,
            last_sync_version=0
        )

    def _find_device(self, user_id: str, device_id: str) -> Optional[Dict]:
        """查找设备"""
        docs, _ = self.repo.query(
            "user_devices",
            {"user_id": user_id, "device_id": device_id},
            limit=1, offset=0
        )
        return docs[0] if docs else None

    # ==================== 基础同步 (Phase 1) ====================

    def basic_sync(
        self,
        user_id: str,
        request: BasicSyncRequest
    ) -> BasicSyncResponse:
        """
        基础同步 - LWW策略
        1. 判断是否需要全量同步
        2. 拉取服务端数据
        3. 返回给客户端
        """
        # 判断同步类型
        sync_type = self._determine_sync_type(user_id, request)

        # 获取同步数据
        if sync_type == SyncType.FULL:
            data = self._get_full_sync_data(user_id)
        else:
            data = self._get_incremental_data(user_id, request.last_sync_at)

        # 更新设备同步状态
        self._update_device_sync_status(user_id, request.device_id)

        return BasicSyncResponse(
            sync_type=sync_type,
            server_time=datetime.utcnow(),
            data=data
        )

    def _determine_sync_type(
        self,
        user_id: str,
        request: BasicSyncRequest
    ) -> SyncType:
        """判断同步类型"""
        # 无上次同步时间 -> 全量
        if not request.last_sync_at:
            return SyncType.FULL

        # 超过阈值天数 -> 全量
        threshold = datetime.utcnow() - timedelta(days=self.FULL_SYNC_THRESHOLD_DAYS)
        if request.last_sync_at < threshold:
            return SyncType.FULL

        # 否则增量
        return SyncType.INCREMENTAL

    def _get_full_sync_data(self, user_id: str) -> Dict[str, Any]:
        """获取全量同步数据"""
        data = {}

        for collection in self.SYNCABLE_COLLECTIONS:
            docs, _ = self.repo.query(
                collection,
                {"user_id": user_id, "_deleted": {"ne": True}},
                limit=10000, offset=0
            )
            data[collection] = docs

        # 用户数据单独处理
        user_docs, _ = self.repo.query("users", {"_id": user_id}, limit=1, offset=0)
        data["users"] = user_docs[0] if user_docs else None

        return data

    def _get_incremental_data(
        self,
        user_id: str,
        since: datetime
    ) -> Dict[str, Any]:
        """获取增量同步数据"""
        data = {}
        since_str = since.isoformat()

        for collection in self.SYNCABLE_COLLECTIONS:
            # 查询自上次同步后更新的数据
            docs, _ = self.repo.query_with_date_filters(
                collection,
                filters={"user_id": user_id},
                date_filters={"_updated_at": {"gt": since_str}},
                limit=10000, offset=0
            )
            data[collection] = docs

        return data

    def _update_device_sync_status(self, user_id: str, device_id: str) -> None:
        """更新设备同步状态"""
        device = self._find_device(user_id, device_id)
        if device:
            device["last_sync_at"] = datetime.utcnow().isoformat()
            self.repo.put("user_devices", device)

    # ==================== 数据上传 ====================

    def upload_changes(
        self,
        user_id: str,
        device_id: str,
        changes: Dict[str, List[Dict]]
    ) -> Dict[str, int]:
        """
        上传本地变更 - LWW策略
        直接覆盖服务端数据（如果本地更新时间更晚）
        """
        stats = {}

        for collection, docs in changes.items():
            if collection not in self.SYNCABLE_COLLECTIONS:
                continue

            updated_count = 0
            for doc in docs:
                # 确保包含用户ID
                doc["user_id"] = user_id
                doc["_device_id"] = device_id

                # LWW: 比较时间戳，本地更新则覆盖
                if self._should_overwrite(collection, doc):
                    doc["_updated_at"] = datetime.utcnow().isoformat()
                    self.repo.put(collection, doc)
                    updated_count += 1

            stats[collection] = updated_count

        return stats

    def _should_overwrite(self, collection: str, local_doc: Dict) -> bool:
        """判断是否应该覆盖服务端数据"""
        doc_id = local_doc.get("id") or local_doc.get("_id")
        if not doc_id:
            return True  # 新文档，直接写入

        # 查询服务端文档
        server_docs, _ = self.repo.query(
            collection, {"id": doc_id}, limit=1, offset=0
        )

        if not server_docs:
            return True  # 服务端不存在，写入

        server_doc = server_docs[0]

        # 比较更新时间
        local_time = local_doc.get("_updated_at", "")
        server_time = server_doc.get("_updated_at", "")

        return local_time >= server_time  # 本地更新或相等时覆盖
```

#### 1.2.2 API 路由

```python
# backend/app/routes/sync.py

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from ..services.sync_service import SyncService
from ..schemas.sync import (
    DeviceRegisterRequest, DeviceRegisterResponse,
    BasicSyncRequest, BasicSyncResponse
)
from ..infra.auth import get_current_user

router = APIRouter(prefix="/sync", tags=["sync"])

def get_sync_service() -> SyncService:
    from ..infra.container import container
    return container.sync_service

# ==================== 设备管理 ====================

@router.post("/devices/register", response_model=DeviceRegisterResponse)
async def register_device(
    request: DeviceRegisterRequest,
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """注册设备"""
    return service.register_device(user_id, request)

@router.get("/devices")
async def list_devices(
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """获取用户所有设备"""
    return service.list_devices(user_id)

# ==================== 基础同步 ====================

@router.post("/pull", response_model=BasicSyncResponse)
async def sync_pull(
    request: BasicSyncRequest,
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """拉取服务端数据"""
    return service.basic_sync(user_id, request)

@router.post("/push")
async def sync_push(
    device_id: str,
    changes: Dict[str, List[Dict]],
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """推送本地变更"""
    stats = service.upload_changes(user_id, device_id, changes)
    return {"status": "ok", "updated": stats}
```

### 1.3 前端实现

#### 1.3.1 本地存储封装

```typescript
// miniprogram/utils/storage.ts

interface StorageData {
  data: any;
  _version: number;
  _updated_at: string;
  _synced: boolean;
}

class StorageManager {
  private static PREFIX = 'sync_';

  /**
   * 保存数据到本地
   */
  static set(collection: string, id: string, data: any): void {
    const key = `${this.PREFIX}${collection}_${id}`;
    const storageData: StorageData = {
      data,
      _version: (data._version || 0) + 1,
      _updated_at: new Date().toISOString(),
      _synced: false
    };

    try {
      wx.setStorageSync(key, storageData);
      // 记录到待同步队列
      this.addToPendingQueue(collection, id, 'update');
    } catch (e) {
      console.error('Storage set failed:', e);
    }
  }

  /**
   * 从本地读取数据
   */
  static get(collection: string, id: string): any {
    const key = `${this.PREFIX}${collection}_${id}`;
    try {
      const storageData = wx.getStorageSync(key) as StorageData;
      return storageData?.data || null;
    } catch (e) {
      console.error('Storage get failed:', e);
      return null;
    }
  }

  /**
   * 删除本地数据（软删除）
   */
  static delete(collection: string, id: string): void {
    const existing = this.get(collection, id);
    if (existing) {
      existing._deleted = true;
      this.set(collection, id, existing);
      this.addToPendingQueue(collection, id, 'delete');
    }
  }

  /**
   * 获取集合所有数据
   */
  static getCollection(collection: string): any[] {
    const prefix = `${this.PREFIX}${collection}_`;
    const result: any[] = [];

    try {
      const info = wx.getStorageInfoSync();
      for (const key of info.keys) {
        if (key.startsWith(prefix)) {
          const storageData = wx.getStorageSync(key) as StorageData;
          if (storageData?.data && !storageData.data._deleted) {
            result.push(storageData.data);
          }
        }
      }
    } catch (e) {
      console.error('Get collection failed:', e);
    }

    return result;
  }

  /**
   * 添加到待同步队列
   */
  private static addToPendingQueue(
    collection: string,
    id: string,
    action: 'create' | 'update' | 'delete'
  ): void {
    const queue = this.getPendingQueue();
    const key = `${collection}:${id}`;

    queue[key] = {
      collection,
      id,
      action,
      timestamp: new Date().toISOString()
    };

    wx.setStorageSync('pending_sync_queue', queue);
  }

  /**
   * 获取待同步队列
   */
  static getPendingQueue(): Record<string, any> {
    try {
      return wx.getStorageSync('pending_sync_queue') || {};
    } catch {
      return {};
    }
  }

  /**
   * 清空待同步队列
   */
  static clearPendingQueue(): void {
    wx.setStorageSync('pending_sync_queue', {});
  }

  /**
   * 获取上次同步时间
   */
  static getLastSyncTime(): string | null {
    try {
      return wx.getStorageSync('last_sync_at') || null;
    } catch {
      return null;
    }
  }

  /**
   * 设置上次同步时间
   */
  static setLastSyncTime(time: string): void {
    wx.setStorageSync('last_sync_at', time);
  }

  /**
   * 批量更新（从服务端同步）
   */
  static batchUpdate(collection: string, docs: any[]): void {
    for (const doc of docs) {
      const id = doc.id || doc._id;
      if (!id) continue;

      const key = `${this.PREFIX}${collection}_${id}`;
      const storageData: StorageData = {
        data: doc,
        _version: doc._version || 1,
        _updated_at: doc._updated_at || new Date().toISOString(),
        _synced: true  // 来自服务端的数据标记为已同步
      };

      wx.setStorageSync(key, storageData);
    }
  }
}

export { StorageManager };
```

#### 1.3.2 同步服务

```typescript
// miniprogram/services/sync.ts

import { request } from './request';
import { StorageManager } from '../utils/storage';

interface SyncConfig {
  autoSyncInterval: number;  // 自动同步间隔（毫秒）
  collections: string[];     // 需要同步的集合
}

interface SyncResult {
  success: boolean;
  syncType: 'full' | 'incremental';
  uploadedCount: number;
  downloadedCount: number;
  error?: string;
}

class SyncService {
  private deviceId: string;
  private config: SyncConfig;
  private syncTimer: number | null = null;
  private isSyncing: boolean = false;

  constructor() {
    this.deviceId = this.getOrCreateDeviceId();
    this.config = {
      autoSyncInterval: 5 * 60 * 1000,  // 5分钟
      collections: [
        'user_vocabulary',
        'scenario_progress',
        'learning_plans',
        'assessments'
      ]
    };
  }

  /**
   * 获取或创建设备ID
   */
  private getOrCreateDeviceId(): string {
    let deviceId = wx.getStorageSync('device_id');
    if (!deviceId) {
      deviceId = this.generateDeviceId();
      wx.setStorageSync('device_id', deviceId);
    }
    return deviceId;
  }

  private generateDeviceId(): string {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 10);
    return `wx_${timestamp}_${random}`;
  }

  /**
   * 注册设备
   */
  async registerDevice(): Promise<void> {
    const systemInfo = wx.getSystemInfoSync();

    await request.post('/sync/devices/register', {
      device_info: {
        device_id: this.deviceId,
        device_type: 'miniprogram',
        device_name: `${systemInfo.brand} ${systemInfo.model}`,
        device_model: systemInfo.model,
        app_version: '1.0.0',
        os_version: systemInfo.system
      }
    });
  }

  /**
   * 执行完整同步
   */
  async sync(): Promise<SyncResult> {
    if (this.isSyncing) {
      return {
        success: false,
        syncType: 'incremental',
        uploadedCount: 0,
        downloadedCount: 0,
        error: 'Sync already in progress'
      };
    }

    this.isSyncing = true;

    try {
      // Step 1: 上传本地变更
      const uploadedCount = await this.pushChanges();

      // Step 2: 拉取服务端数据
      const pullResult = await this.pullChanges();

      // Step 3: 更新本地同步时间
      StorageManager.setLastSyncTime(pullResult.serverTime);

      return {
        success: true,
        syncType: pullResult.syncType,
        uploadedCount,
        downloadedCount: pullResult.downloadedCount
      };
    } catch (error: any) {
      console.error('Sync failed:', error);
      return {
        success: false,
        syncType: 'incremental',
        uploadedCount: 0,
        downloadedCount: 0,
        error: error.message
      };
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * 上传本地变更
   */
  private async pushChanges(): Promise<number> {
    const pendingQueue = StorageManager.getPendingQueue();
    const changes: Record<string, any[]> = {};

    // 按集合分组
    for (const [key, item] of Object.entries(pendingQueue)) {
      const { collection, id } = item;
      if (!changes[collection]) {
        changes[collection] = [];
      }

      const data = StorageManager.get(collection, id);
      if (data) {
        changes[collection].push({ id, ...data });
      }
    }

    // 无变更则跳过
    if (Object.keys(changes).length === 0) {
      return 0;
    }

    // 上传到服务端
    const result = await request.post('/sync/push', {
      device_id: this.deviceId,
      changes
    });

    // 清空队列
    StorageManager.clearPendingQueue();

    // 计算上传数量
    let count = 0;
    for (const num of Object.values(result.updated as Record<string, number>)) {
      count += num;
    }

    return count;
  }

  /**
   * 拉取服务端数据
   */
  private async pullChanges(): Promise<{
    syncType: 'full' | 'incremental';
    serverTime: string;
    downloadedCount: number;
  }> {
    const lastSyncAt = StorageManager.getLastSyncTime();

    const response = await request.post<{
      sync_type: string;
      server_time: string;
      data: Record<string, any[]>;
    }>('/sync/pull', {
      device_id: this.deviceId,
      last_sync_at: lastSyncAt
    });

    // 更新本地存储
    let downloadedCount = 0;
    for (const [collection, docs] of Object.entries(response.data)) {
      if (docs && Array.isArray(docs)) {
        StorageManager.batchUpdate(collection, docs);
        downloadedCount += docs.length;
      }
    }

    return {
      syncType: response.sync_type as 'full' | 'incremental',
      serverTime: response.server_time,
      downloadedCount
    };
  }

  /**
   * 启动自动同步
   */
  startAutoSync(): void {
    if (this.syncTimer) return;

    this.syncTimer = setInterval(() => {
      this.sync().catch(console.error);
    }, this.config.autoSyncInterval) as unknown as number;

    console.log('Auto sync started');
  }

  /**
   * 停止自动同步
   */
  stopAutoSync(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
      console.log('Auto sync stopped');
    }
  }

  /**
   * App 生命周期钩子
   */
  onAppShow(): void {
    // 进入前台时立即同步
    this.sync().catch(console.error);
    this.startAutoSync();
  }

  onAppHide(): void {
    // 进入后台时上传本地变更
    this.pushChanges().catch(console.error);
    this.stopAutoSync();
  }
}

// 导出单例
export const syncService = new SyncService();
```

#### 1.3.3 App.js 集成

```typescript
// miniprogram/app.ts (部分)

import { syncService } from './services/sync';

App({
  onLaunch() {
    // 注册设备
    syncService.registerDevice().catch(console.error);
  },

  onShow() {
    // 进入前台时同步
    syncService.onAppShow();
  },

  onHide() {
    // 进入后台时上传
    syncService.onAppHide();
  }
});
```

### 1.4 Phase 1 检查清单

- [ ] 后端: `sync.py` 领域模型
- [ ] 后端: `sync_service.py` 同步服务
- [ ] 后端: `sync.py` API 路由
- [ ] 后端: 注册路由到 main.py
- [ ] 前端: `storage.ts` 本地存储封装
- [ ] 前端: `sync.ts` 同步服务
- [ ] 前端: App 生命周期集成
- [ ] 测试: 设备注册接口
- [ ] 测试: 基础 pull/push 接口
- [ ] 测试: 离线后同步恢复

---

## Phase 2: 增量同步协议

> **目标**: 基于版本号的高效增量同步
> **工作量**: 5-7 天
> **前置**: Phase 1 完成

### 2.1 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                     版本号机制                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  全局版本号 (Global Version):                                │
│  ├── 每个用户维护独立的版本序列                              │
│  ├── 任何数据变更都会递增版本号                              │
│  └── 客户端通过版本号获取增量变更                            │
│                                                             │
│  示例:                                                       │
│  ┌─────┬────────────────────────────────────────┐           │
│  │ Ver │ 变更内容                               │           │
│  ├─────┼────────────────────────────────────────┤           │
│  │ 100 │ 添加词汇 "passport"                    │           │
│  │ 101 │ 更新场景进度 (airport)                 │           │
│  │ 102 │ 删除词汇 "hello"                       │           │
│  │ 103 │ 更新学习计划                           │           │
│  └─────┴────────────────────────────────────────┘           │
│                                                             │
│  客户端: "给我 version > 100 的所有变更"                     │
│  服务端: 返回 [101, 102, 103] 三条变更                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据结构

#### 2.2.1 sync_changes 表结构

```python
# backend/app/domain/sync.py (扩展)

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum

class ChangeAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class SyncChange(BaseModel):
    """同步变更记录"""
    id: Optional[str] = None
    user_id: str
    entity_type: str          # 集合名称: user_vocabulary, scenario_progress 等
    entity_id: str            # 文档ID
    action: ChangeAction      # 操作类型
    version: int              # 全局版本号
    data: Optional[Dict[str, Any]] = None  # 变更后的数据 (delete时为空)
    previous_version: Optional[int] = None  # 变更前的版本 (用于冲突检测)
    device_id: str            # 发起变更的设备
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserSyncState(BaseModel):
    """用户同步状态"""
    user_id: str
    current_version: int = 0  # 当前最新版本号
    last_compacted_at: Optional[datetime] = None  # 上次压缩时间
```

#### 2.2.2 增量同步请求/响应

```python
# backend/app/schemas/sync.py (扩展)

class IncrementalSyncRequest(BaseModel):
    """增量同步请求"""
    device_id: str
    last_sync_version: int  # 客户端已同步到的版本
    local_changes: List[LocalChange] = []  # 本地变更

class LocalChange(BaseModel):
    """本地变更"""
    entity_type: str
    entity_id: str
    action: str  # create/update/delete
    data: Optional[Dict] = None
    local_version: int  # 本地版本号
    local_updated_at: str

class IncrementalSyncResponse(BaseModel):
    """增量同步响应"""
    server_version: int  # 服务端当前版本
    changes: List[SyncChangeDTO]  # 需要应用的变更
    conflicts: List[ConflictDTO]  # 冲突列表
    acknowledged: List[str]  # 成功接收的本地变更ID

class SyncChangeDTO(BaseModel):
    """变更记录DTO"""
    entity_type: str
    entity_id: str
    action: str
    version: int
    data: Optional[Dict] = None

class ConflictDTO(BaseModel):
    """冲突信息"""
    entity_type: str
    entity_id: str
    local_data: Dict
    server_data: Dict
    server_version: int
    resolution: str  # auto_resolved / needs_manual
```

### 2.3 后端实现

#### 2.3.1 版本管理服务

```python
# backend/app/services/sync_service.py (扩展 - 新增方法)

class SyncService:
    # ... Phase 1 的代码 ...

    # ==================== Phase 2: 增量同步 ====================

    def get_user_version(self, user_id: str) -> int:
        """获取用户当前版本号"""
        docs, _ = self.repo.query(
            "user_sync_state",
            {"user_id": user_id},
            limit=1, offset=0
        )
        if docs:
            return docs[0].get("current_version", 0)
        return 0

    def increment_version(self, user_id: str) -> int:
        """递增并返回新版本号"""
        current = self.get_user_version(user_id)
        new_version = current + 1

        self.repo.put("user_sync_state", {
            "user_id": user_id,
            "current_version": new_version,
            "updated_at": datetime.utcnow().isoformat()
        })

        return new_version

    def record_change(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        action: ChangeAction,
        data: Optional[Dict],
        device_id: str
    ) -> int:
        """记录变更并返回版本号"""
        version = self.increment_version(user_id)

        change_record = {
            "user_id": user_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action.value,
            "version": version,
            "data": data,
            "device_id": device_id,
            "created_at": datetime.utcnow().isoformat()
        }

        self.repo.put("sync_changes", change_record)
        return version

    def incremental_sync(
        self,
        user_id: str,
        request: IncrementalSyncRequest
    ) -> IncrementalSyncResponse:
        """
        增量同步处理
        1. 处理本地变更（检测冲突）
        2. 返回服务端增量变更
        """
        conflicts = []
        acknowledged = []

        # Step 1: 处理本地变更
        for local_change in request.local_changes:
            result = self._process_local_change(
                user_id,
                request.device_id,
                local_change
            )

            if result["status"] == "conflict":
                conflicts.append(result["conflict"])
            else:
                acknowledged.append(local_change.entity_id)

        # Step 2: 获取服务端增量变更
        server_changes = self._get_changes_since(
            user_id,
            request.last_sync_version,
            exclude_device=request.device_id  # 排除当前设备的变更
        )

        # Step 3: 更新设备同步状态
        current_version = self.get_user_version(user_id)
        self._update_device_sync_version(
            user_id,
            request.device_id,
            current_version
        )

        return IncrementalSyncResponse(
            server_version=current_version,
            changes=server_changes,
            conflicts=conflicts,
            acknowledged=acknowledged
        )

    def _process_local_change(
        self,
        user_id: str,
        device_id: str,
        change: LocalChange
    ) -> Dict:
        """处理单个本地变更"""
        # 获取服务端当前数据
        server_doc = self._get_entity(change.entity_type, change.entity_id, user_id)

        # 检测冲突
        if server_doc:
            server_version = server_doc.get("_version", 0)
            server_updated = server_doc.get("_updated_at", "")

            # 冲突条件: 服务端版本更高，且不是同一设备的修改
            if (server_version > change.local_version and
                server_doc.get("_device_id") != device_id):

                # 返回冲突信息（Phase 3 处理具体合并）
                return {
                    "status": "conflict",
                    "conflict": ConflictDTO(
                        entity_type=change.entity_type,
                        entity_id=change.entity_id,
                        local_data=change.data,
                        server_data=server_doc,
                        server_version=server_version,
                        resolution="needs_manual"
                    )
                }

        # 无冲突，应用变更
        self._apply_change(user_id, device_id, change)

        return {"status": "ok"}

    def _apply_change(
        self,
        user_id: str,
        device_id: str,
        change: LocalChange
    ) -> None:
        """应用变更到服务端"""
        action = ChangeAction(change.action)

        if action == ChangeAction.DELETE:
            # 软删除
            data = {"_deleted": True}
        else:
            data = change.data or {}

        # 添加元数据
        version = self.increment_version(user_id)
        data.update({
            "user_id": user_id,
            "_version": version,
            "_updated_at": datetime.utcnow().isoformat(),
            "_device_id": device_id
        })

        # 写入数据
        self.repo.put(change.entity_type, data)

        # 记录变更日志
        self.record_change(
            user_id=user_id,
            entity_type=change.entity_type,
            entity_id=change.entity_id,
            action=action,
            data=data,
            device_id=device_id
        )

    def _get_changes_since(
        self,
        user_id: str,
        since_version: int,
        exclude_device: Optional[str] = None,
        limit: int = 1000
    ) -> List[SyncChangeDTO]:
        """获取指定版本后的变更"""
        filters = {"user_id": user_id}

        # 查询变更记录
        docs, _ = self.repo.query_with_date_filters(
            "sync_changes",
            filters=filters,
            date_filters={"version": {"gt": since_version}},
            limit=limit,
            offset=0
        )

        # 过滤和转换
        changes = []
        for doc in docs:
            # 排除当前设备的变更（已在本地）
            if exclude_device and doc.get("device_id") == exclude_device:
                continue

            changes.append(SyncChangeDTO(
                entity_type=doc["entity_type"],
                entity_id=doc["entity_id"],
                action=doc["action"],
                version=doc["version"],
                data=doc.get("data")
            ))

        # 按版本号排序
        changes.sort(key=lambda x: x.version)

        return changes

    def _get_entity(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """获取实体数据"""
        docs, _ = self.repo.query(
            entity_type,
            {"id": entity_id, "user_id": user_id},
            limit=1, offset=0
        )
        return docs[0] if docs else None

    def _update_device_sync_version(
        self,
        user_id: str,
        device_id: str,
        version: int
    ) -> None:
        """更新设备同步版本"""
        device = self._find_device(user_id, device_id)
        if device:
            device["last_sync_version"] = version
            device["last_sync_at"] = datetime.utcnow().isoformat()
            self.repo.put("user_devices", device)

    # ==================== 变更日志压缩 ====================

    def compact_changes(self, user_id: str, keep_days: int = 30) -> int:
        """
        压缩变更日志
        - 保留最近 N 天的变更
        - 对于同一实体的多次变更，只保留最新
        """
        cutoff = datetime.utcnow() - timedelta(days=keep_days)
        cutoff_str = cutoff.isoformat()

        # 获取旧变更
        old_changes, _ = self.repo.query_with_date_filters(
            "sync_changes",
            filters={"user_id": user_id},
            date_filters={"created_at": {"lt": cutoff_str}},
            limit=10000, offset=0
        )

        # 按实体分组，保留最新
        entity_latest: Dict[str, Dict] = {}
        for change in old_changes:
            key = f"{change['entity_type']}:{change['entity_id']}"
            existing = entity_latest.get(key)
            if not existing or change["version"] > existing["version"]:
                entity_latest[key] = change

        # 删除旧变更（除了每个实体的最新）
        deleted_count = 0
        for change in old_changes:
            key = f"{change['entity_type']}:{change['entity_id']}"
            if entity_latest.get(key) != change:
                self.repo.delete("sync_changes", change["id"])
                deleted_count += 1

        return deleted_count
```

#### 2.3.2 新增 API 端点

```python
# backend/app/routes/sync.py (扩展)

@router.post("/incremental", response_model=IncrementalSyncResponse)
async def incremental_sync(
    request: IncrementalSyncRequest,
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """增量同步"""
    return service.incremental_sync(user_id, request)

@router.get("/version")
async def get_version(
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """获取当前版本号"""
    return {"version": service.get_user_version(user_id)}

@router.get("/changes")
async def get_changes(
    since_version: int = 0,
    limit: int = 100,
    user_id: str = Depends(get_current_user),
    service: SyncService = Depends(get_sync_service)
):
    """获取变更历史"""
    changes = service._get_changes_since(user_id, since_version, limit=limit)
    return {"changes": changes}
```

### 2.4 前端实现

#### 2.4.1 增量同步客户端

```typescript
// miniprogram/services/sync.ts (扩展)

interface LocalChange {
  entity_type: string;
  entity_id: string;
  action: 'create' | 'update' | 'delete';
  data?: any;
  local_version: number;
  local_updated_at: string;
}

interface IncrementalSyncResult {
  serverVersion: number;
  appliedChanges: number;
  conflicts: ConflictInfo[];
}

interface ConflictInfo {
  entityType: string;
  entityId: string;
  localData: any;
  serverData: any;
  resolution: string;
}

class SyncService {
  // ... Phase 1 代码 ...

  private lastSyncVersion: number = 0;

  constructor() {
    // ... Phase 1 初始化 ...
    this.lastSyncVersion = this.getLastSyncVersion();
  }

  private getLastSyncVersion(): number {
    return wx.getStorageSync('last_sync_version') || 0;
  }

  private setLastSyncVersion(version: number): void {
    this.lastSyncVersion = version;
    wx.setStorageSync('last_sync_version', version);
  }

  /**
   * 增量同步 (Phase 2)
   */
  async incrementalSync(): Promise<IncrementalSyncResult> {
    if (this.isSyncing) {
      throw new Error('Sync already in progress');
    }

    this.isSyncing = true;

    try {
      // 收集本地变更
      const localChanges = this.collectLocalChanges();

      // 发送增量同步请求
      const response = await request.post<{
        server_version: number;
        changes: any[];
        conflicts: any[];
        acknowledged: string[];
      }>('/sync/incremental', {
        device_id: this.deviceId,
        last_sync_version: this.lastSyncVersion,
        local_changes: localChanges
      });

      // 应用服务端变更
      let appliedCount = 0;
      for (const change of response.changes) {
        await this.applyServerChange(change);
        appliedCount++;
      }

      // 处理已确认的变更
      this.clearAcknowledgedChanges(response.acknowledged);

      // 更新版本号
      this.setLastSyncVersion(response.server_version);

      // 转换冲突信息
      const conflicts = response.conflicts.map(c => ({
        entityType: c.entity_type,
        entityId: c.entity_id,
        localData: c.local_data,
        serverData: c.server_data,
        resolution: c.resolution
      }));

      return {
        serverVersion: response.server_version,
        appliedChanges: appliedCount,
        conflicts
      };
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * 收集本地变更
   */
  private collectLocalChanges(): LocalChange[] {
    const pendingQueue = StorageManager.getPendingQueue();
    const changes: LocalChange[] = [];

    for (const [key, item] of Object.entries(pendingQueue)) {
      const data = StorageManager.get(item.collection, item.id);

      changes.push({
        entity_type: item.collection,
        entity_id: item.id,
        action: item.action,
        data: item.action === 'delete' ? undefined : data,
        local_version: data?._version || 0,
        local_updated_at: item.timestamp
      });
    }

    return changes;
  }

  /**
   * 应用服务端变更
   */
  private async applyServerChange(change: any): Promise<void> {
    const { entity_type, entity_id, action, data } = change;

    if (action === 'delete') {
      // 删除本地数据
      StorageManager.delete(entity_type, entity_id);
    } else {
      // 更新本地数据（标记为已同步）
      const key = `sync_${entity_type}_${entity_id}`;
      wx.setStorageSync(key, {
        data,
        _version: data._version,
        _updated_at: data._updated_at,
        _synced: true
      });
    }
  }

  /**
   * 清除已确认的变更
   */
  private clearAcknowledgedChanges(acknowledgedIds: string[]): void {
    const queue = StorageManager.getPendingQueue();
    const acknowledgedSet = new Set(acknowledgedIds);

    const newQueue: Record<string, any> = {};
    for (const [key, item] of Object.entries(queue)) {
      if (!acknowledgedSet.has(item.id)) {
        newQueue[key] = item;
      }
    }

    wx.setStorageSync('pending_sync_queue', newQueue);
  }

  /**
   * 强制全量同步
   */
  async forceFullSync(): Promise<void> {
    this.setLastSyncVersion(0);
    StorageManager.clearPendingQueue();
    await this.sync();
  }
}
```

### 2.5 Phase 2 检查清单

- [ ] 后端: `user_sync_state` 集合
- [ ] 后端: `sync_changes` 变更记录
- [ ] 后端: 版本号管理方法
- [ ] 后端: `incremental_sync` 接口
- [ ] 后端: 变更日志压缩任务
- [ ] 前端: 增量同步逻辑
- [ ] 前端: 本地变更收集
- [ ] 前端: 服务端变更应用
- [ ] 测试: 版本号递增正确性
- [ ] 测试: 增量拉取完整性
- [ ] 测试: 并发变更处理

---

## Phase 3: 差异化合并策略

> **目标**: 按数据类型实现智能合并，最大化保留用户数据
> **工作量**: 5-7 天
> **前置**: Phase 2 完成

### 3.1 合并策略概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         合并策略矩阵                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  集合                │ 策略          │ 说明                             │
│  ────────────────────┼───────────────┼────────────────────────────────  │
│  user_vocabulary     │ MERGE + LWW   │ 添加合并，修改取最新              │
│  scenario_progress   │ MAX_VALUE     │ 进度取最大值                     │
│  learning_plans      │ SERVER_WINS   │ 计划以服务端为准                  │
│  assessments         │ SERVER_WINS   │ 评估结果不可变                   │
│  users.stats         │ CUSTOM_MERGE  │ streak 智能合并                  │
│  users.preferences   │ LWW           │ 设置取最后修改                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 合并策略实现

#### 3.2.1 策略基类与注册

```python
# backend/app/services/merge_strategies.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

class MergeResult(str, Enum):
    LOCAL_WINS = "local_wins"
    SERVER_WINS = "server_wins"
    MERGED = "merged"
    CONFLICT = "conflict"

class MergeStrategy(ABC):
    """合并策略基类"""

    @abstractmethod
    def merge(
        self,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Tuple[MergeResult, Dict[str, Any]]:
        """
        执行合并
        返回: (合并结果类型, 合并后的数据)
        """
        pass

    def _get_updated_at(self, data: Dict) -> datetime:
        """获取更新时间"""
        updated_at = data.get("_updated_at", "")
        if isinstance(updated_at, str):
            return datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return updated_at or datetime.min


class MergeStrategyRegistry:
    """合并策略注册表"""

    _strategies: Dict[str, MergeStrategy] = {}

    @classmethod
    def register(cls, entity_type: str, strategy: MergeStrategy):
        cls._strategies[entity_type] = strategy

    @classmethod
    def get(cls, entity_type: str) -> MergeStrategy:
        return cls._strategies.get(entity_type, LWWStrategy())

    @classmethod
    def merge(
        cls,
        entity_type: str,
        local_data: Dict,
        server_data: Dict
    ) -> Tuple[MergeResult, Dict]:
        strategy = cls.get(entity_type)
        return strategy.merge(local_data, server_data)
```

#### 3.2.2 LWW 策略 (Last Write Wins)

```python
# backend/app/services/merge_strategies.py (续)

class LWWStrategy(MergeStrategy):
    """最后写入获胜策略"""

    def merge(
        self,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Tuple[MergeResult, Dict[str, Any]]:
        local_time = self._get_updated_at(local_data)
        server_time = self._get_updated_at(server_data)

        if local_time >= server_time:
            return MergeResult.LOCAL_WINS, local_data
        else:
            return MergeResult.SERVER_WINS, server_data
```

#### 3.2.3 MERGE 策略 (词汇合并)

```python
# backend/app/services/merge_strategies.py (续)

class VocabularyMergeStrategy(MergeStrategy):
    """
    词汇合并策略
    - 新增词汇: 保留双方
    - 修改词汇: LWW
    - 删除词汇: 需要双方都删除才真删
    """

    def merge(
        self,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Tuple[MergeResult, Dict[str, Any]]:
        # 如果是同一条记录的更新
        if local_data.get("id") == server_data.get("id"):
            return self._merge_single_vocab(local_data, server_data)

        # 不同记录，这种情况不应该发生在单条合并中
        # 但为了健壮性，返回本地数据
        return MergeResult.LOCAL_WINS, local_data

    def _merge_single_vocab(
        self,
        local: Dict,
        server: Dict
    ) -> Tuple[MergeResult, Dict]:
        """合并单条词汇"""
        merged = server.copy()

        # 处理删除标记
        local_deleted = local.get("_deleted", False)
        server_deleted = server.get("_deleted", False)

        # 只有双方都删除才真删
        if local_deleted and server_deleted:
            merged["_deleted"] = True
            return MergeResult.MERGED, merged

        # 任一方未删除，保留数据
        if local_deleted or server_deleted:
            merged["_deleted"] = False

        # SRS 数据取更好的结果
        local_srs = local.get("srs", {})
        server_srs = server.get("srs", {})

        merged["srs"] = {
            "level": max(local_srs.get("level", 0), server_srs.get("level", 0)),
            "total_reviews": max(
                local_srs.get("total_reviews", 0),
                server_srs.get("total_reviews", 0)
            ),
            "correct_count": max(
                local_srs.get("correct_count", 0),
                server_srs.get("correct_count", 0)
            ),
            # 下次复习时间取更近的
            "next_review_at": min(
                local_srs.get("next_review_at", "9999-12-31"),
                server_srs.get("next_review_at", "9999-12-31")
            ),
            # 上次复习时间取更近的
            "last_review_at": max(
                local_srs.get("last_review_at", ""),
                server_srs.get("last_review_at", "")
            )
        }

        # 笔记合并：如果双方都有笔记且不同，拼接
        local_notes = local.get("notes", "")
        server_notes = server.get("notes", "")
        if local_notes and server_notes and local_notes != server_notes:
            merged["notes"] = f"{server_notes}\n---\n{local_notes}"
        elif local_notes:
            merged["notes"] = local_notes

        # 标签合并：取并集
        local_tags = set(local.get("tags", []))
        server_tags = set(server.get("tags", []))
        merged["tags"] = list(local_tags | server_tags)

        # 更新版本和时间
        merged["_version"] = max(
            local.get("_version", 0),
            server.get("_version", 0)
        ) + 1

        return MergeResult.MERGED, merged
```

#### 3.2.4 MAX_VALUE 策略 (进度合并)

```python
# backend/app/services/merge_strategies.py (续)

class ProgressMaxStrategy(MergeStrategy):
    """
    进度合并策略
    - 计数类字段取最大值
    - 时间类字段取最近
    - 布尔类字段取 True 优先
    """

    def merge(
        self,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Tuple[MergeResult, Dict[str, Any]]:
        merged = server_data.copy()

        # 对话进度合并
        local_dialogues = {
            d["dialogue_id"]: d
            for d in local_data.get("dialogue_progress", [])
        }
        server_dialogues = {
            d["dialogue_id"]: d
            for d in server_data.get("dialogue_progress", [])
        }

        merged_dialogues = []
        all_dialogue_ids = set(local_dialogues.keys()) | set(server_dialogues.keys())

        for dialogue_id in all_dialogue_ids:
            local_d = local_dialogues.get(dialogue_id, {})
            server_d = server_dialogues.get(dialogue_id, {})

            merged_d = {
                "dialogue_id": dialogue_id,
                "listen_count": max(
                    local_d.get("listen_count", 0),
                    server_d.get("listen_count", 0)
                ),
                "follow_read_attempts": max(
                    local_d.get("follow_read_attempts", 0),
                    server_d.get("follow_read_attempts", 0)
                ),
                "best_score": max(
                    local_d.get("best_score", 0),
                    server_d.get("best_score", 0)
                ),
                "last_score": max(
                    local_d.get("last_score", 0),
                    server_d.get("last_score", 0)
                ),
                "mastered": local_d.get("mastered", False) or server_d.get("mastered", False),
                "last_practiced": max(
                    local_d.get("last_practiced", ""),
                    server_d.get("last_practiced", "")
                )
            }
            merged_dialogues.append(merged_d)

        merged["dialogue_progress"] = merged_dialogues

        # 词汇进度合并
        local_vocab = local_data.get("vocabulary_progress", {})
        server_vocab = server_data.get("vocabulary_progress", {})

        merged["vocabulary_progress"] = {
            "total": max(local_vocab.get("total", 0), server_vocab.get("total", 0)),
            "learned": max(local_vocab.get("learned", 0), server_vocab.get("learned", 0)),
            "mastered": max(local_vocab.get("mastered", 0), server_vocab.get("mastered", 0)),
            "review_due": max(local_vocab.get("review_due", 0), server_vocab.get("review_due", 0))
        }

        # 时间统计合并
        local_time = local_data.get("time_spent", {})
        server_time = server_data.get("time_spent", {})

        merged["time_spent"] = {
            "total_minutes": max(
                local_time.get("total_minutes", 0),
                server_time.get("total_minutes", 0)
            ),
            "listen": max(local_time.get("listen", 0), server_time.get("listen", 0)),
            "follow_read": max(local_time.get("follow_read", 0), server_time.get("follow_read", 0)),
            "vocab_review": max(local_time.get("vocab_review", 0), server_time.get("vocab_review", 0)),
            "practice": max(local_time.get("practice", 0), server_time.get("practice", 0))
        }

        # 就绪度取最高
        merged["readiness"] = max(
            local_data.get("readiness", 0),
            server_data.get("readiness", 0)
        )

        # 完成状态：任一方完成则完成
        merged["completed"] = local_data.get("completed", False) or server_data.get("completed", False)

        return MergeResult.MERGED, merged
```

#### 3.2.5 CUSTOM_MERGE 策略 (用户统计)

```python
# backend/app/services/merge_strategies.py (续)

class UserStatsMergeStrategy(MergeStrategy):
    """
    用户统计合并策略
    - streak: 智能判断
    - 累计值: 取最大
    """

    def merge(
        self,
        local_data: Dict[str, Any],
        server_data: Dict[str, Any]
    ) -> Tuple[MergeResult, Dict[str, Any]]:
        merged = server_data.copy()

        local_stats = local_data.get("stats", {})
        server_stats = server_data.get("stats", {})

        # 累计值取最大
        merged_stats = {
            "total_study_minutes": max(
                local_stats.get("total_study_minutes", 0),
                server_stats.get("total_study_minutes", 0)
            ),
            "total_scenarios_completed": max(
                local_stats.get("total_scenarios_completed", 0),
                server_stats.get("total_scenarios_completed", 0)
            ),
            "total_vocab_mastered": max(
                local_stats.get("total_vocab_mastered", 0),
                server_stats.get("total_vocab_mastered", 0)
            ),
            "longest_streak": max(
                local_stats.get("longest_streak", 0),
                server_stats.get("longest_streak", 0)
            )
        }

        # Streak 智能合并
        local_streak = local_stats.get("current_streak", 0)
        server_streak = server_stats.get("current_streak", 0)
        local_last_study = local_stats.get("last_study_date", "")
        server_last_study = server_stats.get("last_study_date", "")

        # 如果最后学习日期相同，取较大的 streak
        if local_last_study == server_last_study:
            merged_stats["current_streak"] = max(local_streak, server_streak)
            merged_stats["last_study_date"] = local_last_study
        else:
            # 日期不同，取更近日期的数据
            if local_last_study > server_last_study:
                merged_stats["current_streak"] = local_streak
                merged_stats["last_study_date"] = local_last_study
            else:
                merged_stats["current_streak"] = server_streak
                merged_stats["last_study_date"] = server_last_study

        # 更新 longest_streak
        merged_stats["longest_streak"] = max(
            merged_stats["longest_streak"],
            merged_stats["current_streak"]
        )

        merged["stats"] = merged_stats

        return MergeResult.MERGED, merged
```

#### 3.2.6 注册策略

```python
# backend/app/services/merge_strategies.py (续)

# 注册所有策略
MergeStrategyRegistry.register("user_vocabulary", VocabularyMergeStrategy())
MergeStrategyRegistry.register("scenario_progress", ProgressMaxStrategy())
MergeStrategyRegistry.register("learning_plans", LWWStrategy())  # SERVER_WINS 在服务端处理
MergeStrategyRegistry.register("assessments", LWWStrategy())
MergeStrategyRegistry.register("users", UserStatsMergeStrategy())
```

### 3.3 集成到同步服务

```python
# backend/app/services/sync_service.py (修改 _process_local_change 方法)

from .merge_strategies import MergeStrategyRegistry, MergeResult

class SyncService:
    # ... 之前的代码 ...

    def _process_local_change(
        self,
        user_id: str,
        device_id: str,
        change: LocalChange
    ) -> Dict:
        """处理单个本地变更 (Phase 3: 使用合并策略)"""
        server_doc = self._get_entity(change.entity_type, change.entity_id, user_id)

        if not server_doc:
            # 服务端不存在，直接写入
            self._apply_change(user_id, device_id, change)
            return {"status": "ok"}

        # 检查版本
        server_version = server_doc.get("_version", 0)
        if server_version <= change.local_version:
            # 本地版本更新或相等，直接写入
            self._apply_change(user_id, device_id, change)
            return {"status": "ok"}

        # 有冲突，使用合并策略
        result, merged_data = MergeStrategyRegistry.merge(
            change.entity_type,
            change.data or {},
            server_doc
        )

        if result == MergeResult.CONFLICT:
            # 无法自动解决，返回冲突
            return {
                "status": "conflict",
                "conflict": ConflictDTO(
                    entity_type=change.entity_type,
                    entity_id=change.entity_id,
                    local_data=change.data,
                    server_data=server_doc,
                    server_version=server_version,
                    resolution="needs_manual"
                )
            }

        # 自动合并成功，写入合并后的数据
        merged_data["user_id"] = user_id
        merged_data["_device_id"] = device_id
        merged_data["_updated_at"] = datetime.utcnow().isoformat()

        self.repo.put(change.entity_type, merged_data)

        # 记录变更
        self.record_change(
            user_id=user_id,
            entity_type=change.entity_type,
            entity_id=change.entity_id,
            action=ChangeAction.UPDATE,
            data=merged_data,
            device_id=device_id
        )

        return {
            "status": "auto_merged",
            "merged_data": merged_data,
            "merge_result": result.value
        }
```

### 3.4 前端冲突处理 UI

```typescript
// miniprogram/components/conflict-resolver/conflict-resolver.ts

interface ConflictInfo {
  entityType: string;
  entityId: string;
  localData: any;
  serverData: any;
}

Component({
  properties: {
    conflict: {
      type: Object,
      value: null
    }
  },

  data: {
    showModal: false,
    conflictDescription: '',
    options: [] as Array<{ label: string; value: string }>
  },

  observers: {
    'conflict': function(conflict: ConflictInfo) {
      if (conflict) {
        this.prepareConflictDisplay(conflict);
        this.setData({ showModal: true });
      }
    }
  },

  methods: {
    prepareConflictDisplay(conflict: ConflictInfo) {
      const descriptions: Record<string, string> = {
        'user_vocabulary': '词汇数据冲突',
        'scenario_progress': '学习进度冲突',
        'learning_plans': '学习计划冲突'
      };

      this.setData({
        conflictDescription: descriptions[conflict.entityType] || '数据冲突',
        options: [
          { label: '使用本地数据', value: 'local' },
          { label: '使用服务器数据', value: 'server' },
          { label: '合并两者', value: 'merge' }
        ]
      });
    },

    onSelectOption(e: any) {
      const { value } = e.currentTarget.dataset;
      this.triggerEvent('resolve', {
        conflict: this.properties.conflict,
        resolution: value
      });
      this.setData({ showModal: false });
    },

    onClose() {
      this.setData({ showModal: false });
      this.triggerEvent('cancel');
    }
  }
});
```

### 3.5 Phase 3 检查清单

- [ ] 后端: `merge_strategies.py` 策略基类
- [ ] 后端: `LWWStrategy` 实现
- [ ] 后端: `VocabularyMergeStrategy` 实现
- [ ] 后端: `ProgressMaxStrategy` 实现
- [ ] 后端: `UserStatsMergeStrategy` 实现
- [ ] 后端: 策略注册和集成
- [ ] 后端: 修改 `_process_local_change`
- [ ] 前端: 冲突解决组件
- [ ] 前端: 手动解决流程
- [ ] 测试: 各策略单元测试
- [ ] 测试: 复杂冲突场景测试
- [ ] 测试: 边界条件测试

---

## 测试方案

### 单元测试

```python
# backend/tests/test_sync_service.py

import pytest
from datetime import datetime, timedelta
from app.services.sync_service import SyncService
from app.services.merge_strategies import (
    VocabularyMergeStrategy,
    ProgressMaxStrategy,
    MergeResult
)

class TestVocabularyMerge:
    """词汇合并策略测试"""

    def test_srs_level_takes_max(self):
        """SRS等级取最大值"""
        strategy = VocabularyMergeStrategy()

        local = {
            "id": "vocab_1",
            "word": "hello",
            "srs": {"level": 3, "total_reviews": 5},
            "_updated_at": "2025-01-01T10:00:00"
        }
        server = {
            "id": "vocab_1",
            "word": "hello",
            "srs": {"level": 5, "total_reviews": 3},
            "_updated_at": "2025-01-01T09:00:00"
        }

        result, merged = strategy.merge(local, server)

        assert result == MergeResult.MERGED
        assert merged["srs"]["level"] == 5  # 取最大
        assert merged["srs"]["total_reviews"] == 5  # 取最大

    def test_tags_union(self):
        """标签取并集"""
        strategy = VocabularyMergeStrategy()

        local = {"id": "v1", "tags": ["travel", "basic"], "_updated_at": "2025-01-01"}
        server = {"id": "v1", "tags": ["basic", "business"], "_updated_at": "2025-01-01"}

        result, merged = strategy.merge(local, server)

        assert set(merged["tags"]) == {"travel", "basic", "business"}

    def test_delete_requires_both(self):
        """删除需要双方都删除"""
        strategy = VocabularyMergeStrategy()

        local = {"id": "v1", "_deleted": True, "_updated_at": "2025-01-01"}
        server = {"id": "v1", "_deleted": False, "_updated_at": "2025-01-01"}

        result, merged = strategy.merge(local, server)

        assert merged["_deleted"] == False  # 保留


class TestProgressMaxMerge:
    """进度合并策略测试"""

    def test_listen_count_max(self):
        """听力次数取最大"""
        strategy = ProgressMaxStrategy()

        local = {
            "dialogue_progress": [
                {"dialogue_id": "d1", "listen_count": 10, "mastered": False}
            ]
        }
        server = {
            "dialogue_progress": [
                {"dialogue_id": "d1", "listen_count": 5, "mastered": True}
            ]
        }

        result, merged = strategy.merge(local, server)

        assert merged["dialogue_progress"][0]["listen_count"] == 10
        assert merged["dialogue_progress"][0]["mastered"] == True  # True 优先


class TestStreakMerge:
    """连续天数合并测试"""

    def test_same_date_takes_higher_streak(self):
        """相同日期取更高streak"""
        from app.services.merge_strategies import UserStatsMergeStrategy
        strategy = UserStatsMergeStrategy()

        local = {"stats": {"current_streak": 5, "last_study_date": "2025-01-15"}}
        server = {"stats": {"current_streak": 3, "last_study_date": "2025-01-15"}}

        result, merged = strategy.merge(local, server)

        assert merged["stats"]["current_streak"] == 5

    def test_different_date_takes_newer(self):
        """不同日期取更近的"""
        from app.services.merge_strategies import UserStatsMergeStrategy
        strategy = UserStatsMergeStrategy()

        local = {"stats": {"current_streak": 1, "last_study_date": "2025-01-16"}}
        server = {"stats": {"current_streak": 10, "last_study_date": "2025-01-10"}}

        result, merged = strategy.merge(local, server)

        assert merged["stats"]["current_streak"] == 1  # 取更近日期的
        assert merged["stats"]["last_study_date"] == "2025-01-16"
```

### 集成测试场景

```python
# backend/tests/test_sync_integration.py

class TestSyncIntegration:
    """同步集成测试"""

    async def test_offline_24h_then_sync(self):
        """离线24小时后同步"""
        # 1. 设备A在线，添加10个词汇
        # 2. 设备A离线
        # 3. 设备B登录，添加5个不同词汇
        # 4. 24小时后，设备A上线同步
        # 5. 验证: 15个词汇都存在
        pass

    async def test_concurrent_progress_update(self):
        """并发进度更新"""
        # 1. 设备A学习对话1，listen_count=5
        # 2. 设备B同时学习对话1，listen_count=3，但完成mastered=True
        # 3. 同步后验证: listen_count=5, mastered=True
        pass

    async def test_streak_across_timezone(self):
        """跨时区streak处理"""
        # 1. 设备A在UTC+8学习，streak=5，日期=2025-01-15
        # 2. 设备B在UTC-5学习，streak=6，日期=2025-01-14
        # 3. 同步后验证: streak=5 (更近日期的数据)
        pass
```

---

## 部署检查清单

### Phase 1 部署

- [ ] CloudBase 创建 `user_devices` 集合
- [ ] CloudBase 创建索引: `user_id`, `device_id`
- [ ] 部署 `/sync/*` API 路由
- [ ] 小程序更新 `sync.ts` 服务
- [ ] 测试设备注册流程
- [ ] 测试基础同步流程

### Phase 2 部署

- [ ] CloudBase 创建 `sync_changes` 集合
- [ ] CloudBase 创建 `user_sync_state` 集合
- [ ] CloudBase 创建索引: `user_id + version`
- [ ] 部署增量同步 API
- [ ] 配置变更日志压缩定时任务
- [ ] 灰度发布增量同步功能

### Phase 3 部署

- [ ] 部署合并策略代码
- [ ] 小程序发布冲突解决组件
- [ ] 监控合并冲突率
- [ ] 收集用户反馈
- [ ] 根据反馈调整合并策略

---

## 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| sync_success_rate | 同步成功率 | < 95% |
| sync_latency_p99 | 同步延迟 P99 | > 5s |
| conflict_rate | 冲突率 | > 5% |
| auto_merge_rate | 自动合并成功率 | < 90% |
| sync_changes_count | 变更日志数量 | > 100万/用户 |

---

*文档版本: v1.0*
*创建日期: 2025-12-29*
*最后更新: 2025-12-29*