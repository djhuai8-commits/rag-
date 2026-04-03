# 一键启动脚本（Windows PowerShell）

$ErrorActionPreference = "Stop"

Write-Host "🚀 企业知识库智能问答系统 — 一键启动" -ForegroundColor Cyan

# 检查 .env
if (-Not (Test-Path ".env")) {
    Write-Host "📋 未找到 .env，正在从模板创建..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  请先编辑 .env 填写 LLM_API_KEY 和 SECRET_KEY，然后重新运行此脚本" -ForegroundColor Red
    exit 1
}

# 检查 Docker
if (-Not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ 未检测到 Docker，请先安装 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "📦 启动所有服务..." -ForegroundColor Green
docker compose up -d --build

Write-Host ""
Write-Host "✅ 启动完成！" -ForegroundColor Green
Write-Host "   前端地址：http://localhost"
Write-Host "   API 文档：http://localhost/docs"
Write-Host "   健康检查：http://localhost/health"
Write-Host ""
Write-Host "   默认账号：admin / admin123"
Write-Host ""
Write-Host "📝 查看日志：docker compose logs -f backend"
