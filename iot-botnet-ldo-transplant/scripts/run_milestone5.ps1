$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------------------
# Milestone 5 - Random-Split Baseline Batch Runner
#
# 2 datasets × 3 models × 3 seeds = 18 runs
#
# Datasets:
#   nbaiot
#   medbiot
#
# Models:
#   ensemble
#   autoencoder
#   cnn
#
# Seeds:
#   42, 43, 44
#
# Random split:
#   80/20 stratified
#
# Controlled sample size:
#   160,000 training rows
#    40,000 test rows
#
# Neural network:
#   5 epochs
#   batch size 256
#
# Results:
#   results/raw_metrics.csv
#
# Log:
#   results/milestone5_batch.log
# ---------------------------------------------------------------------------

# Repository root = parent of the scripts directory.
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$TrainScript = Join-Path $ProjectRoot "src\train.py"
$ResultsDir = Join-Path $ProjectRoot "results"
$ResultsFile = Join-Path $ResultsDir "raw_metrics.csv"
$LogFile = Join-Path $ResultsDir "milestone5_batch.log"

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

$Datasets = @(
    "nbaiot",
    "medbiot"
)

$Models = @(
    "ensemble",
    "autoencoder",
    "cnn"
)

$Seeds = @(
    42,
    43,
    44
)

$TrainRows = 160000
$TestRows = 40000

$TestSize = 0.20

$Epochs = 5
$BatchSize = 256

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

Write-Host "Project root : $ProjectRoot"
Write-Host "Train script : $TrainScript"

if (-not (Test-Path $TrainScript)) {
    throw "Training script not found: $TrainScript"
}

New-Item -ItemType Directory -Force $ResultsDir | Out-Null

# ---------------------------------------------------------------------------
# Start clean
# ---------------------------------------------------------------------------
# Remove any temporary/incomplete Milestone 5 results.
# The final CSV must contain exactly 18 experiment rows.

if (Test-Path $ResultsFile) {
    Remove-Item $ResultsFile -Force
}

if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force
}

$StartTime = Get-Date

Add-Content $LogFile "============================================================"
Add-Content $LogFile "Milestone 5 Random-Split Batch"
Add-Content $LogFile "Started: $StartTime"
Add-Content $LogFile "============================================================"
Add-Content $LogFile ""

$totalRuns = $Datasets.Count * $Models.Count * $Seeds.Count
$currentRun = 0

# ---------------------------------------------------------------------------
# Run all 18 experiments
# ---------------------------------------------------------------------------

foreach ($dataset in $Datasets) {

    foreach ($model in $Models) {

        foreach ($seed in $Seeds) {

            $currentRun++

            $header = @"
========================================================================
Milestone 5 Run $currentRun / $totalRuns
Dataset : $dataset
Model   : $model
Seed    : $seed
Train   : $TrainRows rows
Test    : $TestRows rows
========================================================================
"@

            Write-Host $header
            Add-Content $LogFile $header

            $arguments = @(
                $TrainScript
                "--model", $model
                "--dataset", $dataset
                "--split", "random"
                "--test-size", $TestSize
                "--random-state", $seed
                "--max-train-rows", $TrainRows
                "--max-test-rows", $TestRows
                "--epochs", $Epochs
                "--batch-size", $BatchSize
                "--output", $ResultsFile
            )

            # ---------------------------------------------------------------
            # Important PowerShell behavior:
            #
            # Python/TensorFlow writes informational warnings to STDERR.
            # They must NOT terminate this batch script.
            #
            # Actual Python failures are detected using $LASTEXITCODE below.
            # ---------------------------------------------------------------

            & python -u @arguments 2>&1 |
                Tee-Object -FilePath $LogFile -Append

            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {

                $message = @"
========================================================================
FAILED
Run       : $currentRun / $totalRuns
Dataset   : $dataset
Model     : $model
Seed      : $seed
Exit code : $exitCode
========================================================================
"@

                Write-Host $message
                Add-Content $LogFile $message

                throw "Milestone 5 batch stopped because this run failed."
            }

            Add-Content $LogFile ""
        }
    }
}

# ---------------------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------------------

if (-not (Test-Path $ResultsFile)) {
    throw "Expected results file was not created: $ResultsFile"
}

$ResultLines = Get-Content $ResultsFile

# Header + 18 result rows = 19 lines.
$ExpectedLines = $totalRuns + 1

if ($ResultLines.Count -ne $ExpectedLines) {
    throw (
        "Expected $totalRuns result rows, " +
        "but raw_metrics.csv contains " +
        ($ResultLines.Count - 1) +
        " result rows."
    )
}

$EndTime = Get-Date

$summary = @"
========================================================================
Milestone 5 batch completed successfully
========================================================================
Runs completed : $totalRuns / $totalRuns
Started        : $StartTime
Finished       : $EndTime
Results        : $ResultsFile
Log            : $LogFile
========================================================================
"@

Write-Host $summary
Add-Content $LogFile ""
Add-Content $LogFile $summary