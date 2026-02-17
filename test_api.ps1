# API Testing Guide - Manual Testing with REST API
# ==================================================

# STEP 1: Start the API Server
# -----------------------------
Write-Host "🚀 Starting API Server..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Run this in a separate terminal:" -ForegroundColor Yellow
Write-Host "   python -m uvicorn api.main:app --reload --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Wait for: 'Application startup complete'" -ForegroundColor Green
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key when server is ready..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# STEP 2: Submit Application
# ---------------------------
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "📝 STEP 1: SUBMIT APPLICATION" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

Write-Host "Submitting applicant from sample_applicant.json..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications" `
        -Method Post `
        -ContentType "application/json" `
        -InFile "sample_applicant.json" `
        -TimeoutSec 30
    
    Write-Host "✅ Application submitted successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Application ID: $($response.application_id)" -ForegroundColor Cyan
    Write-Host "Applicant: $($response.applicant_name)" -ForegroundColor White
    Write-Host "Status: $($response.status)" -ForegroundColor Yellow
    Write-Host ""
    
    $applicationId = $response.application_id
    
} catch {
    Write-Host "❌ Error submitting application: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "  1. API server is running (python -m uvicorn api.main:app --reload)" -ForegroundColor White
    Write-Host "  2. sample_applicant.json exists" -ForegroundColor White
    exit 1
}

# STEP 3: Run Screening
# ----------------------
Write-Host "Press any key to run screening..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "🔍 STEP 2: RUN SCREENING (8 AI AGENTS)" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

Write-Host "Running full AI screening workflow..." -ForegroundColor Yellow
Write-Host "This will execute all 8 agents in 5 phases..." -ForegroundColor Gray
Write-Host ""

try {
    $screeningResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications/$applicationId/screen" `
        -Method Post `
        -TimeoutSec 60
    
    Write-Host "✅ Screening complete!" -ForegroundColor Green
    Write-Host ""
    
    # Display results
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host "📊 SCREENING RESULTS" -ForegroundColor White
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host ""
    
    # Decision
    $decision = $screeningResponse.decision
    $decisionEmoji = if ($decision -eq "APPROVE") { "✅" } elseif ($decision -eq "CONDITIONAL") { "⚠️" } else { "❌" }
    Write-Host "🎯 FINAL DECISION: $decisionEmoji $decision" -ForegroundColor $(if ($decision -eq "APPROVE") { "Green" } elseif ($decision -eq "CONDITIONAL") { "Yellow" } else { "Red" })
    Write-Host "   Confidence: $($screeningResponse.confidence)%" -ForegroundColor White
    Write-Host ""
    
    # Identity
    Write-Host "👤 Identity Verification:" -ForegroundColor Cyan
    Write-Host "   Status: $($screeningResponse.identity_status)" -ForegroundColor White
    Write-Host "   Confidence: $($screeningResponse.identity_confidence)%" -ForegroundColor White
    Write-Host ""
    
    # Risk
    Write-Host "📈 Risk Assessment:" -ForegroundColor Cyan
    Write-Host "   Risk Score: $($screeningResponse.risk_score)/1000" -ForegroundColor White
    Write-Host "   Risk Tier: $($screeningResponse.risk_tier)" -ForegroundColor White
    Write-Host ""
    
    # Fraud
    Write-Host "🚨 Fraud Assessment:" -ForegroundColor Cyan
    Write-Host "   Risk Level: $($screeningResponse.fraud_risk_level)" -ForegroundColor White
    Write-Host ""
    
    # Compliance
    Write-Host "⚖️  Compliance:" -ForegroundColor Cyan
    Write-Host "   FCRA: $(if ($screeningResponse.fcra_compliant) { '✅ Compliant' } else { '❌ Non-Compliant' })" -ForegroundColor White
    Write-Host "   Fair Housing: $(if ($screeningResponse.fair_housing_compliant) { '✅ Compliant' } else { '❌ Non-Compliant' })" -ForegroundColor White
    Write-Host ""
    
    # Bias
    Write-Host "🎭 Fairness:" -ForegroundColor Cyan
    Write-Host "   Bias Detected: $(if ($screeningResponse.bias_detected) { '⚠️ Yes' } else { '✅ No' })" -ForegroundColor White
    Write-Host "   Fairness Score: $($screeningResponse.fairness_score)%" -ForegroundColor White
    Write-Host ""
    
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Error running screening: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# STEP 4: Get Full Results
# -------------------------
Write-Host ""
Write-Host "Press any key to view full detailed results..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "📋 STEP 3: DETAILED RESULTS" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

try {
    $detailedResults = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/applications/$applicationId/results" `
        -Method Get `
        -TimeoutSec 30
    
    Write-Host ($detailedResults | ConvertTo-Json -Depth 10)
    Write-Host ""
    
    Write-Host "✅ Full results retrieved!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error getting results: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host "✨ TESTING COMPLETE!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 78) -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Modify sample_applicant.json with your test data" -ForegroundColor White
Write-Host "   2. Run this script again: .\test_api.ps1" -ForegroundColor White
Write-Host "   3. Or use Postman/Insomnia with http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Interactive API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
