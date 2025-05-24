# PowerShell script to deploy to Vercel
Write-Host "Deploying webhook system to Vercel..." -ForegroundColor Cyan

# Make sure the app directory is included
if (!(Test-Path "app")) {
    Write-Host "Error: app directory not found!" -ForegroundColor Red
    exit 1
}

# Verify the email_service.py file exists and contains the os import
$emailServicePath = "app/services/email_service.py"
if (!(Test-Path $emailServicePath)) {
    Write-Host "Error: $emailServicePath not found!" -ForegroundColor Red
    exit 1
}

Write-Host "Verifying email_service.py imports..." -ForegroundColor Yellow
$emailServiceContent = Get-Content $emailServicePath -Raw
if (!($emailServiceContent -match "import os")) {
    Write-Host "Error: os import not found in email_service.py!" -ForegroundColor Red
    exit 1
}

Write-Host "Verified imports are correct." -ForegroundColor Green

# Deploy to production
Write-Host "`nDeploying to Vercel..." -ForegroundColor Yellow
vercel --prod

Write-Host "`nDeployment complete! Please verify:" -ForegroundColor Green
Write-Host "1. Check deployment logs in Vercel dashboard" -ForegroundColor Yellow
Write-Host "2. Test the webhook endpoint" -ForegroundColor Yellow
Write-Host "3. Verify email sending works" -ForegroundColor Yellow

Write-Host "`nTest the deployment with: python updated_test_order.py" -ForegroundColor Cyan
