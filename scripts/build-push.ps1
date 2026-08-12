# Build and push with a DISTINCT tag from sales-reports-email (won't overwrite that image).
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

$Image = "phanindra004/skylark-chicks-delivery-sms:latest"

Write-Host "Building $Image (no cache)..." -ForegroundColor Cyan
docker build --no-cache -t $Image .

Write-Host "Pushing $Image..." -ForegroundColor Cyan
docker push $Image

Write-Host "Done. On VM run:" -ForegroundColor Green
Write-Host "  docker pull $Image"
Write-Host "  docker stop skylark-chicks-delivery-sms; docker rm skylark-chicks-delivery-sms"
Write-Host @"
  docker run -d --name skylark-chicks-delivery-sms --restart unless-stopped ``
    -e TZ=Asia/Kolkata ``
    -e MSSQL_SERVER=117.239.10.139 ``
    -e MSSQL_PORT=1433 ``
    -e MSSQL_DATABASE=SkylarkLive-2025 ``
    -e MSSQL_USER=Mobapp2 ``
    -e MSSQL_PASSWORD='Shiv@971#' ``
    $Image
"@
