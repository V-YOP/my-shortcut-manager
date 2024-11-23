# 使用 Python 解释器运行脚本
$scriptPath = Join-Path $PSScriptRoot "sm"
$process = Start-Process -FilePath "python" -ArgumentList $scriptPath + @args -NoNewWindow -PassThru -Wait

# 检查返回值
if ($process.ExitCode -ne 0) {
    Write-Host "Python 脚本返回了错误，错误代码：$($process.ExitCode)" -ForegroundColor Red
    Read-Host "按 Enter 键退出..."
}
