#!/bin/bash

# ============================================================
# 项目部署脚本
# 物联网环境监测系统 - 服务器部署
# ============================================================

set -e

echo "========================================"
echo "  物联网环境监测系统 - 部署脚本"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose 未安装${NC}"
    echo "请先安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env 文件不存在，从 .env.example 创建...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${RED}请编辑 .env 文件，设置正确的数据库密码等配置！${NC}"
        echo "编辑命令: vi .env"
        read -p "配置完成后按回车继续..."
    else
        echo -e "${RED}错误: .env.example 文件不存在${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}1. 停止旧容器...${NC}"
docker-compose down

echo -e "${GREEN}2. 清理旧镜像（可选）...${NC}"
read -p "是否清理旧的 Docker 镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose build --no-cache
else
    docker-compose build
fi

echo -e "${GREEN}3. 启动服务...${NC}"
docker-compose up -d

echo -e "${GREEN}4. 等待服务启动...${NC}"
sleep 10

echo -e "${GREEN}5. 运行数据库迁移...${NC}"
docker-compose exec backend python manage.py migrate

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "访问地址:"
echo "  前端: http://39.105.122.26"
echo "  后端 API: http://39.105.122.26/api/"
echo "  Django Admin: http://39.105.122.26/admin/"
echo "  API 文档: http://39.105.122.26/swagger/"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  查看状态: docker-compose ps"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo -e "${YELLOW}如需创建超级用户，请运行:${NC}"
echo "  docker-compose exec backend python manage.py createsuperuser"
echo ""
