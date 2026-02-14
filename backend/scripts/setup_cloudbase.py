#!/usr/bin/env python3
"""
CloudBase环境配置辅助脚本

用法：
    python scripts/setup_cloudbase.py --check    # 检查配置
    python scripts/setup_cloudbase.py --init     # 初始化集合
    python scripts/setup_cloudbase.py --verify   # 验证连接
"""
import os
import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infra.tcb_client import TCBClient
from app.infra.config import Settings


# 必需的数据库集合
REQUIRED_COLLECTIONS = [
    "users",
    "content",
    "progress",
    "vocab",
    "plans",
    "orders",
    "events",
    "wishlists"
]


class CloudBaseSetup:
    """CloudBase环境配置助手"""

    def __init__(self):
        self.settings = Settings()
        self.client = None

    def check_env_vars(self) -> bool:
        """检查必需的环境变量"""
        print("\n=== 环境变量检查 ===\n")

        required_vars = {
            "REPO_PROVIDER": self.settings.repo_provider,
            "TCB_ENV_ID": self.settings.tcb_env_id,
            "TCB_SECRET_ID": self.settings.tcb_secret_id,
            "TCB_SECRET_KEY": self.settings.tcb_secret_key,
            "TCB_REGION": self.settings.tcb_region,
        }

        all_set = True
        for var_name, value in required_vars.items():
            if value:
                # 隐藏密钥内容
                display_value = value[:8] + "***" if "SECRET" in var_name or "KEY" in var_name else value
                print(f"✅ {var_name}: {display_value}")
            else:
                print(f"❌ {var_name}: 未设置")
                all_set = False

        if not all_set:
            print("\n⚠️  请在 .env 文件或环境变量中设置缺失的配置")
            print("参考模板：backend/.env.example\n")
            return False

        print("\n✅ 所有必需环境变量已设置\n")
        return True

    def verify_connection(self) -> bool:
        """验证CloudBase连接"""
        print("\n=== CloudBase连接验证 ===\n")

        try:
            self.client = TCBClient.from_settings(self.settings)
            print(f"环境ID: {self.settings.tcb_env_id}")
            print(f"区域: {self.settings.tcb_region}")

            # 尝试查询一个集合
            test_collection = "users"
            print(f"\n尝试查询集合: {test_collection}")

            docs, total = self.client.query(test_collection, {}, limit=1, offset=0)
            print(f"✅ 连接成功！查询到 {total} 条记录")
            return True

        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            print("\n可能的原因：")
            print("1. 密钥配置错误")
            print("2. 环境ID不存在")
            print("3. 集合尚未创建")
            print("4. 网络连接问题")
            return False

    def check_collections(self) -> dict:
        """检查数据库集合状态"""
        print("\n=== 数据库集合检查 ===\n")

        if not self.client:
            try:
                self.client = TCBClient.from_settings(self.settings)
            except Exception as e:
                print(f"❌ 无法连接到CloudBase: {str(e)}")
                return {}

        collection_status = {}

        for collection in REQUIRED_COLLECTIONS:
            try:
                docs, total = self.client.query(collection, {}, limit=1, offset=0)
                collection_status[collection] = {
                    "exists": True,
                    "count": total,
                    "status": "✅"
                }
                print(f"✅ {collection}: {total} 条记录")
            except Exception as e:
                error_msg = str(e)
                # 判断是集合不存在还是其他错误
                if "not found" in error_msg.lower() or "不存在" in error_msg:
                    collection_status[collection] = {
                        "exists": False,
                        "count": 0,
                        "status": "❌ 未创建"
                    }
                    print(f"❌ {collection}: 集合不存在")
                else:
                    collection_status[collection] = {
                        "exists": "unknown",
                        "count": 0,
                        "status": f"⚠️  错误: {error_msg[:50]}"
                    }
                    print(f"⚠️  {collection}: {error_msg[:50]}")

        return collection_status

    def generate_collection_creation_guide(self):
        """生成集合创建指南"""
        print("\n=== 集合创建指南 ===\n")
        print("请在CloudBase控制台手动创建以下集合：\n")
        print("登录：https://console.cloud.tencent.com/tcb")
        print(f"环境：{self.settings.tcb_env_id}\n")

        for i, collection in enumerate(REQUIRED_COLLECTIONS, 1):
            print(f"{i}. {collection}")

        print("\n创建步骤：")
        print("1. 进入「数据库」→「集合管理」")
        print("2. 点击「新建集合」")
        print("3. 输入集合名称（如上所示）")
        print("4. 确认创建")
        print("\n创建完成后，运行：python scripts/setup_cloudbase.py --verify\n")

    def generate_security_rules_guide(self):
        """生成安全规则配置指南"""
        print("\n=== 安全规则配置指南 ===\n")

        rules_file = Path(__file__).parent.parent.parent / "cloudbase" / "security.rules.json"

        if rules_file.exists():
            print(f"✅ 安全规则文件存在: {rules_file}")
            print("\n配置步骤：")
            print("1. 登录CloudBase控制台")
            print("2. 进入「数据库」→「安全规则」")
            print("3. 复制以下内容或上传文件\n")

            try:
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                    print(json.dumps(rules, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"读取规则文件失败: {e}")
        else:
            print(f"❌ 安全规则文件不存在: {rules_file}")
            print("请参考文档创建安全规则配置")

    def generate_indexes_guide(self):
        """生成索引创建指南"""
        print("\n=== 索引创建指南 ===\n")

        indexes_file = Path(__file__).parent.parent.parent / "cloudbase" / "collections.indexes.json"

        if indexes_file.exists():
            print(f"✅ 索引配置文件存在: {indexes_file}")
            print("\n关键索引：")

            try:
                with open(indexes_file, 'r', encoding='utf-8') as f:
                    indexes = json.load(f)
                    for collection, index_list in indexes.items():
                        print(f"\n{collection}:")
                        for idx in index_list:
                            fields = ", ".join(idx.get("fields", []))
                            print(f"  - {fields}")
            except Exception as e:
                print(f"读取索引文件失败: {e}")

            print("\n配置步骤：")
            print("1. 登录CloudBase控制台")
            print("2. 进入「数据库」→「索引管理」")
            print("3. 为每个集合创建对应索引")
        else:
            print(f"⚠️  索引配置文件不存在: {indexes_file}")
            print("建议创建索引以提升查询性能")

    def run_full_check(self):
        """运行完整检查"""
        print("\n" + "="*60)
        print("CloudBase环境配置检查")
        print("="*60)

        # 1. 检查环境变量
        if not self.check_env_vars():
            return False

        # 2. 验证连接
        if not self.verify_connection():
            print("\n❌ 连接验证失败，请检查配置")
            return False

        # 3. 检查集合
        collection_status = self.check_collections()

        missing_collections = [
            name for name, status in collection_status.items()
            if not status.get("exists")
        ]

        if missing_collections:
            print(f"\n⚠️  缺少 {len(missing_collections)} 个集合")
            self.generate_collection_creation_guide()
            return False

        # 4. 显示配置指南
        self.generate_security_rules_guide()
        self.generate_indexes_guide()

        print("\n" + "="*60)
        print("✅ CloudBase环境配置完成！")
        print("="*60)
        print("\n下一步：")
        print("1. 配置微信小程序订阅消息")
        print("2. 准备音频资源")
        print("3. 部署后端服务")
        print("4. 提交小程序审核\n")

        return True


def main():
    parser = argparse.ArgumentParser(description="CloudBase环境配置助手")
    parser.add_argument("--check", action="store_true", help="检查配置状态")
    parser.add_argument("--verify", action="store_true", help="验证CloudBase连接")
    parser.add_argument("--collections", action="store_true", help="检查集合状态")
    parser.add_argument("--full", action="store_true", help="运行完整检查")

    args = parser.parse_args()

    setup = CloudBaseSetup()

    if args.check:
        setup.check_env_vars()
    elif args.verify:
        setup.verify_connection()
    elif args.collections:
        setup.check_collections()
    elif args.full:
        setup.run_full_check()
    else:
        # 默认运行完整检查
        setup.run_full_check()


if __name__ == "__main__":
    main()
