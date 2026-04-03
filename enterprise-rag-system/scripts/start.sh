#!/usr/bin/env bash
# 快速启动脚本（Linux / macOS）

set -e

echo "🚀 企业知识库智能问答系统 — 一键启动"

# 检查 .env 是否存在
if [ ! -f ".env" ]; then
  echo "📋 未找到 .env，正在从模板创建..."
  cp .env.example .env
  echo "⚠️  请先编辑 .env 填写 LLM_API_KEY 和 SECRET_KEY，然后重新运行此脚本"
  exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
  echo "❌ 未检测到 Docker，请先安装 Docker Desktop"
  exit 1
fi

echo "📦 拉取镜像并启动服务..."
docker compose pull --ignore-pull-failures
docker compose up -d --build

echo ""
echo "✅ 启动完成！"
echo "   前端地址：http://localhost"
echo "   API 文档：http://localhost/docs"
echo "   健康检查：http://localhost/health"
echo ""
echo "   默认账号：admin / admin123"
echo ""
echo "📝 查看日志：docker compose logs -f backend"
