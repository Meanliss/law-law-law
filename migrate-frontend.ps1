# Migration Script - Replace Old Frontend with React App

Write-Host "🚀 Starting Frontend Migration..." -ForegroundColor Cyan

# Step 1: Xóa frontend cũ
Write-Host "`n📦 Step 1: Removing old frontend..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Remove-Item -Path "frontend" -Recurse -Force
    Write-Host "✅ Old frontend removed" -ForegroundColor Green
}

# Step 2: Copy React app
Write-Host "`n📦 Step 2: Moving React app to frontend/..." -ForegroundColor Yellow
Copy-Item -Path "AI Chatbot for Law Website" -Destination "frontend" -Recurse
Write-Host "✅ React app copied to frontend/" -ForegroundColor Green

# Step 3: Install dependencies
Write-Host "`n📦 Step 3: Installing dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install
npm install @types/react @types/react-dom -D
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Step 4: Create .env file
Write-Host "`n📦 Step 4: Creating .env file..." -ForegroundColor Yellow
@"
VITE_API_URL=http://localhost:7860
"@ | Out-File -FilePath ".env" -Encoding utf8
Write-Host "✅ .env file created" -ForegroundColor Green

# Step 5: Update vite.config.ts
Write-Host "`n📦 Step 5: Configuring Vite proxy..." -ForegroundColor Yellow
@"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:7860',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
"@ | Out-File -FilePath "vite.config.ts" -Encoding utf8
Write-Host "✅ Vite config updated" -ForegroundColor Green

Set-Location ..

Write-Host "`n✨ Migration completed successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. cd frontend" -ForegroundColor White
Write-Host "  2. npm run dev" -ForegroundColor White
Write-Host "  3. Open http://localhost:3000" -ForegroundColor White
