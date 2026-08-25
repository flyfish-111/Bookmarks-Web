#!/usr/bin/env bash
# 网址收藏夹 - 云服务器一键部署脚本
# 用法：在服务器项目目录下执行  bash deploy.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 检查 Docker..."
if ! command -v docker >/dev/null 2>&1; then
  echo "错误：未检测到 Docker。请先安装 Docker 与 Docker Compose 后再运行。"
  exit 1
fi

echo "==> 检查 .env..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "已从 .env.example 生成 .env 文件。"
  echo "请先编辑 .env 修改数据库密码（如 vi .env），再重新运行本脚本。"
  exit 0
fi

echo "==> 构建并启动服务（首次会拉取镜像，较慢）..."
docker compose up -d --build

echo ""
echo "==> 服务状态："
docker compose ps

IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || true)
echo ""
echo "部署完成，访问地址：http://${IP:-<你的服务器IP>}"
