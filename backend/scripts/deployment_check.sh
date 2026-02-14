#!/bin/bash

# ====================================
# 部署前验证脚本
# ====================================
# 用法：bash scripts/deployment_check.sh

set -e

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_NC='\033[0m' # No Color

echo -e "${COLOR_GREEN}=====================================${COLOR_NC}"
echo -e "${COLOR_GREEN}语言学习平台 - 部署前检查${COLOR_NC}"
echo -e "${COLOR_GREEN}=====================================${COLOR_NC}"
echo ""

# 检查Python版本
echo "1. 检查Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${COLOR_GREEN}✓${COLOR_NC} $PYTHON_VERSION"
else
    echo -e "${COLOR_RED}✗ Python3未安装${COLOR_NC}"
    exit 1
fi

# 检查虚拟环境
echo ""
echo "2. 检查虚拟环境..."
if [ -d "venv" ]; then
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 虚拟环境已存在"
else
    echo -e "${COLOR_YELLOW}⚠${COLOR_NC} 虚拟环境不存在，创建中..."
    python3 -m venv venv
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 虚拟环境已创建"
fi

# 激活虚拟环境
echo ""
echo "3. 激活虚拟环境..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 虚拟环境已激活"
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 虚拟环境已激活 (Windows)"
else
    echo -e "${COLOR_RED}✗ 无法激活虚拟环境${COLOR_NC}"
    exit 1
fi

# 安装依赖
echo ""
echo "4. 检查依赖..."
if pip show fastapi &> /dev/null; then
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 依赖已安装"
else
    echo -e "${COLOR_YELLOW}⚠${COLOR_NC} 依赖未安装，安装中..."
    pip install -r requirements.txt
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 依赖安装完成"
fi

# 运行测试
echo ""
echo "5. 运行测试..."
if pytest tests/ -v --tb=short; then
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 所有测试通过"
else
    echo -e "${COLOR_RED}✗ 测试失败${COLOR_NC}"
    exit 1
fi

# 检查环境变量
echo ""
echo "6. 检查环境变量配置..."
if python scripts/setup_cloudbase.py --check; then
    echo -e "${COLOR_GREEN}✓${COLOR_NC} 环境变量配置正确"
else
    echo -e "${COLOR_YELLOW}⚠${COLOR_NC} 环境变量需要配置"
fi

# 验证CloudBase连接
echo ""
echo "7. 验证CloudBase连接..."
if python scripts/setup_cloudbase.py --verify; then
    echo -e "${COLOR_GREEN}✓${COLOR_NC} CloudBase连接成功"
else
    echo -e "${COLOR_YELLOW}⚠${COLOR_NC} CloudBase连接失败，请检查配置"
fi

# 检查集合状态
echo ""
echo "8. 检查数据库集合..."
python scripts/setup_cloudbase.py --collections

echo ""
echo -e "${COLOR_GREEN}=====================================${COLOR_NC}"
echo -e "${COLOR_GREEN}部署检查完成！${COLOR_NC}"
echo -e "${COLOR_GREEN}=====================================${COLOR_NC}"
echo ""
echo "下一步："
echo "1. 确保所有环境变量已配置"
echo "2. 确保所有数据库集合已创建"
echo "3. 配置安全规则和索引"
echo "4. 启动服务：uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
