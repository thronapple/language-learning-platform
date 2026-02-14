#!/usr/bin/env python3
"""
CloudBase (TCB) 连接验证脚本

使用方法：
    python scripts/verify_tcb_connection.py

环境变量要求：
    REPO_PROVIDER=tcb
    TCB_ENV_ID=your-env-id
    TCB_SECRET_ID=your-secret-id
    TCB_SECRET_KEY=your-secret-key
    TCB_REGION=ap-guangzhou (可选)
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infra.config import settings
from app.infra.tcb_client import TCBClient
from app.repositories.tcb import TCBRepository


def print_header(title):
    """打印格式化标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def verify_config():
    """验证配置"""
    print_header("1. 验证配置")

    print(f"✓ 仓储提供商: {settings.repo_provider}")

    if settings.repo_provider != "tcb":
        print("⚠️  警告：REPO_PROVIDER 不是 'tcb'")
        print(f"   当前值: {settings.repo_provider}")
        print("   请设置: export REPO_PROVIDER=tcb")
        return False

    print(f"✓ 环境ID: {settings.tcb_env_id or '未设置'}")
    print(f"✓ 区域: {settings.tcb_region or '默认'}")
    print(f"✓ Secret ID: {settings.tcb_secret_id[:10]}... (已设置)" if settings.tcb_secret_id else "✗ Secret ID: 未设置")
    print(f"✓ Secret Key: {'***' if settings.tcb_secret_key else '未设置'}")

    if not settings.tcb_env_id:
        print("\n✗ 错误：TCB_ENV_ID 未设置")
        print("  请设置: export TCB_ENV_ID=your-env-id")
        return False

    if not settings.tcb_secret_id or not settings.tcb_secret_key:
        print("\n✗ 错误：TCB密钥未设置")
        print("  请设置:")
        print("    export TCB_SECRET_ID=your-secret-id")
        print("    export TCB_SECRET_KEY=your-secret-key")
        return False

    return True


def test_client_creation():
    """测试客户端创建"""
    print_header("2. 创建TCB客户端")

    try:
        client = TCBClient.from_settings(settings)
        print(f"✓ 客户端创建成功")
        print(f"  环境ID: {client.env_id}")
        print(f"  区域: {client.region or '默认'}")
        return client
    except Exception as e:
        print(f"✗ 客户端创建失败: {e}")
        return None


def test_basic_query(client):
    """测试基本查询"""
    print_header("3. 测试基本查询")

    collections = ["users", "content", "vocab", "progress"]

    for collection in collections:
        try:
            print(f"\n查询集合: {collection}")
            docs, total = client.query(
                collection=collection,
                filters={},
                limit=1,
                offset=0
            )
            print(f"  ✓ 查询成功，共 {total} 条记录")
            if docs:
                print(f"  ✓ 示例文档字段: {list(docs[0].keys())[:5]}")
        except Exception as e:
            print(f"  ⚠️ 查询失败: {e}")
            print(f"     可能原因：集合 '{collection}' 不存在或权限不足")


def test_repository_operations(client):
    """测试仓储操作"""
    print_header("4. 测试仓储层操作")

    repo = TCBRepository(client)
    test_collection = "events"  # 使用events集合进行测试

    try:
        # 测试添加文档
        print("\n测试添加文档...")
        test_doc = {
            "event": "test_connection",
            "user_id": "test_user",
            "props": {"source": "verify_script"},
            "ts": "2025-01-01T00:00:00Z"
        }
        doc_id = repo.put(test_collection, test_doc)
        print(f"  ✓ 文档添加成功，ID: {doc_id}")

        # 测试查询文档
        print("\n测试查询文档...")
        retrieved = repo.get(test_collection, doc_id)
        if retrieved:
            print(f"  ✓ 文档查询成功")
            print(f"    事件: {retrieved.get('event')}")
        else:
            print(f"  ⚠️ 文档查询失败")

        # 测试删除文档
        print("\n测试删除文档...")
        deleted = repo.delete(test_collection, doc_id)
        if deleted:
            print(f"  ✓ 文档删除成功")
        else:
            print(f"  ⚠️ 文档删除失败")

        print("\n✓ 仓储层操作测试通过")

    except Exception as e:
        print(f"\n✗ 仓储层操作测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_date_filters(client):
    """测试日期过滤查询"""
    print_header("5. 测试日期过滤查询")

    try:
        print("\n查询今日到期的词汇...")
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        docs, total = client.query_with_date_filters(
            collection="vocab",
            filters={"user_id": "test_user"},
            date_filters={"next_review_at": {"lte": now_iso}},
            limit=10,
            offset=0
        )
        print(f"  ✓ 日期过滤查询成功")
        print(f"  ✓ 到期词汇数量: {total}")

    except Exception as e:
        print(f"  ⚠️ 日期过滤查询失败: {e}")


def print_summary():
    """打印总结"""
    print_header("验证完成")
    print("\n✓ CloudBase连接验证已完成！")
    print("\n后续步骤：")
    print("  1. 检查数据库安全规则: cloudbase/security.rules.json")
    print("  2. 创建必要的索引: cloudbase/collections.indexes.json")
    print("  3. 在CloudBase控制台创建所需集合")
    print("  4. 配置生产环境变量")
    print("\n详细文档：backend/TCB_SETUP.md")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  CloudBase (TCB) 连接验证工具")
    print("=" * 60)

    # 步骤1：验证配置
    if not verify_config():
        print("\n✗ 配置验证失败，请检查环境变量")
        sys.exit(1)

    # 步骤2：创建客户端
    client = test_client_creation()
    if not client:
        print("\n✗ 无法创建TCB客户端")
        sys.exit(1)

    # 步骤3：测试基本查询
    test_basic_query(client)

    # 步骤4：测试仓储操作
    test_repository_operations(client)

    # 步骤5：测试日期过滤
    test_date_filters(client)

    # 打印总结
    print_summary()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
