# Cache Management Script
# Dùng khi thay đổi embedding model hoặc cần rebuild indexes

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('clean', 'info', 'rebuild-faiss', 'rebuild-bm25', 'rebuild-all')]
    [string]$Action = 'info'
)

$CacheDir = "backend\cache"

function Show-CacheInfo {
    Write-Host "`n📊 CACHE INFORMATION" -ForegroundColor Cyan
    Write-Host "=" * 70
    
    if (Test-Path $CacheDir) {
        $files = Get-ChildItem -Path $CacheDir -File
        
        if ($files.Count -eq 0) {
            Write-Host "❌ No cache files found" -ForegroundColor Yellow
            return
        }
        
        foreach ($file in $files) {
            $size = [math]::Round($file.Length / 1MB, 2)
            $modified = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            
            Write-Host "`n📄 $($file.Name)" -ForegroundColor White
            Write-Host "   Size: ${size} MB"
            Write-Host "   Modified: $modified"
            
            # Show dimension if .dim file
            if ($file.Name -like "*.dim") {
                $dim = Get-Content $file.FullName
                Write-Host "   Dimension: $dim" -ForegroundColor Green
            }
            
            # Show hash if .hash file
            if ($file.Name -like "*.hash") {
                $hash = Get-Content $file.FullName
                Write-Host "   Hash: $($hash.Substring(0, 16))..." -ForegroundColor Gray
            }
        }
        
        $totalSize = [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
        Write-Host "`n💾 Total cache size: ${totalSize} MB" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Cache directory not found: $CacheDir" -ForegroundColor Red
    }
    Write-Host "=" * 70
}

function Clean-Cache {
    Write-Host "`n🗑️  CLEANING CACHE" -ForegroundColor Yellow
    Write-Host "=" * 70
    
    if (Test-Path $CacheDir) {
        $files = Get-ChildItem -Path $CacheDir -File
        
        if ($files.Count -eq 0) {
            Write-Host "✅ Cache already empty" -ForegroundColor Green
            return
        }
        
        foreach ($file in $files) {
            Remove-Item $file.FullName -Force
            Write-Host "❌ Deleted: $($file.Name)" -ForegroundColor Red
        }
        
        Write-Host "`n✅ Cache cleaned successfully!" -ForegroundColor Green
        Write-Host "   Next startup will rebuild all indexes" -ForegroundColor Gray
    } else {
        Write-Host "❌ Cache directory not found" -ForegroundColor Red
    }
    Write-Host "=" * 70
}

function Rebuild-FaissCache {
    Write-Host "`n🔄 REBUILDING FAISS INDEX" -ForegroundColor Yellow
    Write-Host "=" * 70
    
    Remove-Item "$CacheDir\embeddings.pkl*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ FAISS cache cleared" -ForegroundColor Green
    Write-Host "   Reason: Embedding model changed" -ForegroundColor Gray
    Write-Host "   Old dimension: 384 (MiniLM)" -ForegroundColor Gray
    Write-Host "   New dimension: 768 (Vietnamese-SBERT)" -ForegroundColor Green
    Write-Host "`n⚠️  Restart backend to rebuild with new model" -ForegroundColor Yellow
    Write-Host "=" * 70
}

function Rebuild-Bm25Cache {
    Write-Host "`n🔄 REBUILDING BM25 INDEX" -ForegroundColor Yellow
    Write-Host "=" * 70
    
    Remove-Item "$CacheDir\bm25_index.pkl*" -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ BM25 cache cleared" -ForegroundColor Green
    Write-Host "   Restart backend to rebuild" -ForegroundColor Gray
    Write-Host "=" * 70
}

function Rebuild-AllCache {
    Write-Host "`n🔄 REBUILDING ALL INDEXES" -ForegroundColor Yellow
    Write-Host "=" * 70
    
    Rebuild-FaissCache
    Write-Host ""
    Rebuild-Bm25Cache
}

# Main
switch ($Action) {
    'info' {
        Show-CacheInfo
    }
    'clean' {
        Clean-Cache
    }
    'rebuild-faiss' {
        Rebuild-FaissCache
    }
    'rebuild-bm25' {
        Rebuild-Bm25Cache
    }
    'rebuild-all' {
        Rebuild-AllCache
    }
}

Write-Host "`n💡 Usage:" -ForegroundColor Cyan
Write-Host "   .\scripts\cache-manage.ps1 info          # Show cache info"
Write-Host "   .\scripts\cache-manage.ps1 clean         # Clean all cache"
Write-Host "   .\scripts\cache-manage.ps1 rebuild-faiss # Rebuild FAISS only"
Write-Host "   .\scripts\cache-manage.ps1 rebuild-bm25  # Rebuild BM25 only"
Write-Host "   .\scripts\cache-manage.ps1 rebuild-all   # Rebuild everything"
Write-Host ""
