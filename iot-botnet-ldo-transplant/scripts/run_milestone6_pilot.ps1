$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------------------
# Milestone 6 - Leave-Device-Out Production Sweep
#
# Milestone 5 baseline:
#   18 random-split rows already exist in results/raw_metrics.csv
#
# Milestone 6 pilot:
#   9 LDO rows for Danmini_Doorbell already exist
#
# This script runs the remaining:
#
#   8 remaining N-BaIoT folds × 3 models × 3 seeds = 72
#   3 MedBIoT folds        × 3 models × 3 seeds = 27
#
# Remaining experiments = 99
#
# Final expected CSV:
#   18 random rows + 108 LDO rows = 126 rows
#
# Configuration:
#   train cap : 160,000
#   test cap  : 40,000
#   epochs    : 5
#   batch size: 256
#   seeds     : 42, 43, 44
#
# Existing results are preserved and new results are appended.
# ---------------------------------------------------------------------------

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$TrainScript = Join-Path $ProjectRoot "src\train.py"
$ResultsDir = Join-Path $ProjectRoot "results"
$ResultsFile = Join-Path $ResultsDir "raw_metrics.csv"
$LogFile = Join-Path $ResultsDir "milestone6_batch.log"

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

$NBaIoTFolds = @(
    "Ecobee_Thermostat",
    "Ennio_Doorbell",
    "Philips_B120N10_Baby_Monitor",
    "Provision_PT_737E_Security_Camera",
    "Provision_PT_838_Security_Camera",
    "Samsung_SNH_1011_N_Webcam",
    "SimpleHome_XCS7_1002_WHT_Security_Camera",
    "SimpleHome_XCS7_1003_WHT_Security_Camera"
)

$MedBIoTFolds = @(
    "fan",
    "light",
    "switch"
)

$TrainRows = 160000
$TestRows = 40000

$Epochs = 5
$BatchSize = 256

# ---------------------------------------------------------------------------
# Expected experiment counts
# ---------------------------------------------------------------------------

$ExpectedBaselineRows = 18
$ExpectedPilotRows = 9
$ExpectedStartingRows = $ExpectedBaselineRows + $ExpectedPilotRows

$ExpectedRemainingRuns = (
    ($NBaIoTFolds.Count + $MedBIoTFolds.Count) *
    $Models.Count *
    $Seeds.Count
)

$ExpectedFinalRows = (
    $ExpectedBaselineRows +
    108
)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

Write-Host "Project root : $ProjectRoot"
Write-Host "Train script : $TrainScript"
Write-Host "Results file : $ResultsFile"

if (-not (Test-Path $TrainScript)) {
    throw "Training script not found: $TrainScript"
}

if (-not (Test-Path $ResultsFile)) {
    throw "Results file not found: $ResultsFile"
}

New-Item -ItemType Directory -Force $ResultsDir | Out-Null

# ---------------------------------------------------------------------------
# Verify the existing 27 rows before starting.
# ---------------------------------------------------------------------------

$ExistingRows = @(Import-Csv $ResultsFile)

if ($ExistingRows.Count -ne $ExpectedStartingRows) {
    throw (
        "Safety check failed. Expected exactly " +
        "$ExpectedStartingRows rows before the production sweep, " +
        "but found $($ExistingRows.Count). " +
        "No experiments were started."
    )
}

$RandomRows = @(
    $ExistingRows |
        Where-Object {
            $_.split_type -eq "random"
        }
)

if ($RandomRows.Count -ne $ExpectedBaselineRows) {
    throw (
        "Expected $ExpectedBaselineRows random-split baseline rows, " +
        "but found $($RandomRows.Count). " +
        "No experiments were started."
    )
}

$PilotRows = @(
    $ExistingRows |
        Where-Object {
            $_.dataset -eq "nbaiot" -and
            $_.split_type -eq "ldo" -and
            $_.fold -eq "Danmini_Doorbell"
        }
)

if ($PilotRows.Count -ne $ExpectedPilotRows) {
    throw (
        "Expected $ExpectedPilotRows Danmini_Doorbell LDO pilot rows, " +
        "but found $($PilotRows.Count). " +
        "No experiments were started."
    )
}

Write-Host "Existing random-split rows verified : $($RandomRows.Count)"
Write-Host "Existing LDO pilot rows verified    : $($PilotRows.Count)"
Write-Host "Starting CSV rows                   : $($ExistingRows.Count)"
Write-Host "Remaining LDO experiments           : $ExpectedRemainingRuns"
Write-Host "Expected final CSV rows             : $ExpectedFinalRows"

# ---------------------------------------------------------------------------
# Start fresh production log.
# ---------------------------------------------------------------------------

if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force
}

$StartTime = Get-Date

Add-Content $LogFile "============================================================"
Add-Content $LogFile "Milestone 6 LDO Production Sweep"
Add-Content $LogFile "Started: $StartTime"
Add-Content $LogFile "============================================================"
Add-Content $LogFile ""

$currentRun = 0

# ---------------------------------------------------------------------------
# N-BaIoT - remaining 8 folds
# ---------------------------------------------------------------------------

foreach ($fold in $NBaIoTFolds) {

    foreach ($model in $Models) {

        foreach ($seed in $Seeds) {

            $currentRun++

            $header = @"
========================================================================
Milestone 6 Run $currentRun / $ExpectedRemainingRuns
Dataset : nbaiot
Fold    : $fold
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
                "--dataset", "nbaiot"
                "--split", "ldo"
                "--fold", $fold
                "--random-state", $seed
                "--max-train-rows", $TrainRows
                "--max-test-rows", $TestRows
                "--epochs", $Epochs
                "--batch-size", $BatchSize
                "--output", $ResultsFile
            )

            & python -u @arguments 2>&1 |
                Tee-Object -FilePath $LogFile -Append

            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {

                $message = @"
========================================================================
FAILED
Run       : $currentRun / $ExpectedRemainingRuns
Dataset   : nbaiot
Fold      : $fold
Model     : $model
Seed      : $seed
Exit code : $exitCode
========================================================================
"@

                Write-Host $message
                Add-Content $LogFile $message

                throw "Milestone 6 production sweep stopped because this run failed."
            }

            Add-Content $LogFile ""
        }
    }
}

# ---------------------------------------------------------------------------
# MedBIoT - all 3 folds
# ---------------------------------------------------------------------------

foreach ($fold in $MedBIoTFolds) {

    foreach ($model in $Models) {

        foreach ($seed in $Seeds) {

            $currentRun++

            $header = @"
========================================================================
Milestone 6 Run $currentRun / $ExpectedRemainingRuns
Dataset : medbiot
Fold    : $fold
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
                "--dataset", "medbiot"
                "--split", "ldo"
                "--fold", $fold
                "--random-state", $seed
                "--max-train-rows", $TrainRows
                "--max-test-rows", $TestRows
                "--epochs", $Epochs
                "--batch-size", $BatchSize
                "--output", $ResultsFile
            )

            & python -u @arguments 2>&1 |
                Tee-Object -FilePath $LogFile -Append

            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {

                $message = @"
========================================================================
FAILED
Run       : $currentRun / $ExpectedRemainingRuns
Dataset   : medbiot
Fold      : $fold
Model     : $model
Seed      : $seed
Exit code : $exitCode
========================================================================
"@

                Write-Host $message
                Add-Content $LogFile $message

                throw "Milestone 6 production sweep stopped because this run failed."
            }

            Add-Content $LogFile ""
        }
    }
}

# ---------------------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------------------

if ($currentRun -ne $ExpectedRemainingRuns) {
    throw (
        "Expected $ExpectedRemainingRuns production runs, " +
        "but completed $currentRun."
    )
}

$FinalRows = @(Import-Csv $ResultsFile)

if ($FinalRows.Count -ne $ExpectedFinalRows) {
    throw (
        "Expected $ExpectedFinalRows total CSV rows " +
        "(18 random + 108 LDO), " +
        "but found $($FinalRows.Count)."
    )
}

$FinalRandomRows = @(
    $FinalRows |
        Where-Object {
            $_.split_type -eq "random"
        }
)

$FinalLDORows = @(
    $FinalRows |
        Where-Object {
            $_.split_type -eq "ldo"
        }
)

if ($FinalRandomRows.Count -ne 18) {
    throw (
        "Final validation failed: expected 18 random-split rows, " +
        "found $($FinalRandomRows.Count)."
    )
}

if ($FinalLDORows.Count -ne 108) {
    throw (
        "Final validation failed: expected 108 LDO rows, " +
        "found $($FinalLDORows.Count)."
    )
}

$EndTime = Get-Date

$summary = @"
========================================================================
Milestone 6 LDO production sweep completed successfully
========================================================================
Runs completed      : $currentRun / $ExpectedRemainingRuns
Random baseline     : $($FinalRandomRows.Count) rows
LDO results         : $($FinalLDORows.Count) rows
Total CSV rows      : $($FinalRows.Count)
Started             : $StartTime
Finished            : $EndTime
Results             : $ResultsFile
Log                 : $LogFile
========================================================================
"@

Write-Host $summary
Add-Content $LogFile ""
Add-Content $LogFile $summary$ErrorActionPreference = "Continue"

# ---------------------------------------------------------------------------
# Milestone 6 - Leave-Device-Out Production Sweep
#
# Milestone 5 baseline:
#   18 random-split rows already exist in results/raw_metrics.csv
#
# Milestone 6 pilot:
#   9 LDO rows for Danmini_Doorbell already exist
#
# This script runs the remaining:
#
#   8 remaining N-BaIoT folds × 3 models × 3 seeds = 72
#   3 MedBIoT folds        × 3 models × 3 seeds = 27
#
# Remaining experiments = 99
#
# Final expected CSV:
#   18 random rows + 108 LDO rows = 126 rows
#
# Configuration:
#   train cap : 160,000
#   test cap  : 40,000
#   epochs    : 5
#   batch size: 256
#   seeds     : 42, 43, 44
#
# Existing results are preserved and new results are appended.
# ---------------------------------------------------------------------------

$ProjectRoot = Split-Path -Parent $PSScriptRoot

$TrainScript = Join-Path $ProjectRoot "src\train.py"
$ResultsDir = Join-Path $ProjectRoot "results"
$ResultsFile = Join-Path $ResultsDir "raw_metrics.csv"
$LogFile = Join-Path $ResultsDir "milestone6_batch.log"

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

$NBaIoTFolds = @(
    "Ecobee_Thermostat",
    "Ennio_Doorbell",
    "Philips_B120N10_Baby_Monitor",
    "Provision_PT_737E_Security_Camera",
    "Provision_PT_838_Security_Camera",
    "Samsung_SNH_1011_N_Webcam",
    "SimpleHome_XCS7_1002_WHT_Security_Camera",
    "SimpleHome_XCS7_1003_WHT_Security_Camera"
)

$MedBIoTFolds = @(
    "fan",
    "light",
    "switch"
)

$TrainRows = 160000
$TestRows = 40000

$Epochs = 5
$BatchSize = 256

# ---------------------------------------------------------------------------
# Expected experiment counts
# ---------------------------------------------------------------------------

$ExpectedBaselineRows = 18
$ExpectedPilotRows = 9
$ExpectedStartingRows = $ExpectedBaselineRows + $ExpectedPilotRows

$ExpectedRemainingRuns = (
    ($NBaIoTFolds.Count + $MedBIoTFolds.Count) *
    $Models.Count *
    $Seeds.Count
)

$ExpectedFinalRows = (
    $ExpectedBaselineRows +
    108
)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

Write-Host "Project root : $ProjectRoot"
Write-Host "Train script : $TrainScript"
Write-Host "Results file : $ResultsFile"

if (-not (Test-Path $TrainScript)) {
    throw "Training script not found: $TrainScript"
}

if (-not (Test-Path $ResultsFile)) {
    throw "Results file not found: $ResultsFile"
}

New-Item -ItemType Directory -Force $ResultsDir | Out-Null

# ---------------------------------------------------------------------------
# Verify the existing 27 rows before starting.
# ---------------------------------------------------------------------------

$ExistingRows = @(Import-Csv $ResultsFile)

if ($ExistingRows.Count -ne $ExpectedStartingRows) {
    throw (
        "Safety check failed. Expected exactly " +
        "$ExpectedStartingRows rows before the production sweep, " +
        "but found $($ExistingRows.Count). " +
        "No experiments were started."
    )
}

$RandomRows = @(
    $ExistingRows |
        Where-Object {
            $_.split_type -eq "random"
        }
)

if ($RandomRows.Count -ne $ExpectedBaselineRows) {
    throw (
        "Expected $ExpectedBaselineRows random-split baseline rows, " +
        "but found $($RandomRows.Count). " +
        "No experiments were started."
    )
}

$PilotRows = @(
    $ExistingRows |
        Where-Object {
            $_.dataset -eq "nbaiot" -and
            $_.split_type -eq "ldo" -and
            $_.fold -eq "Danmini_Doorbell"
        }
)

if ($PilotRows.Count -ne $ExpectedPilotRows) {
    throw (
        "Expected $ExpectedPilotRows Danmini_Doorbell LDO pilot rows, " +
        "but found $($PilotRows.Count). " +
        "No experiments were started."
    )
}

Write-Host "Existing random-split rows verified : $($RandomRows.Count)"
Write-Host "Existing LDO pilot rows verified    : $($PilotRows.Count)"
Write-Host "Starting CSV rows                   : $($ExistingRows.Count)"
Write-Host "Remaining LDO experiments           : $ExpectedRemainingRuns"
Write-Host "Expected final CSV rows             : $ExpectedFinalRows"

# ---------------------------------------------------------------------------
# Start fresh production log.
# ---------------------------------------------------------------------------

if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force
}

$StartTime = Get-Date

Add-Content $LogFile "============================================================"
Add-Content $LogFile "Milestone 6 LDO Production Sweep"
Add-Content $LogFile "Started: $StartTime"
Add-Content $LogFile "============================================================"
Add-Content $LogFile ""

$currentRun = 0

# ---------------------------------------------------------------------------
# N-BaIoT - remaining 8 folds
# ---------------------------------------------------------------------------

foreach ($fold in $NBaIoTFolds) {

    foreach ($model in $Models) {

        foreach ($seed in $Seeds) {

            $currentRun++

            $header = @"
========================================================================
Milestone 6 Run $currentRun / $ExpectedRemainingRuns
Dataset : nbaiot
Fold    : $fold
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
                "--dataset", "nbaiot"
                "--split", "ldo"
                "--fold", $fold
                "--random-state", $seed
                "--max-train-rows", $TrainRows
                "--max-test-rows", $TestRows
                "--epochs", $Epochs
                "--batch-size", $BatchSize
                "--output", $ResultsFile
            )

            & python -u @arguments 2>&1 |
                Tee-Object -FilePath $LogFile -Append

            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {

                $message = @"
========================================================================
FAILED
Run       : $currentRun / $ExpectedRemainingRuns
Dataset   : nbaiot
Fold      : $fold
Model     : $model
Seed      : $seed
Exit code : $exitCode
========================================================================
"@

                Write-Host $message
                Add-Content $LogFile $message

                throw "Milestone 6 production sweep stopped because this run failed."
            }

            Add-Content $LogFile ""
        }
    }
}

# ---------------------------------------------------------------------------
# MedBIoT - all 3 folds
# ---------------------------------------------------------------------------

foreach ($fold in $MedBIoTFolds) {

    foreach ($model in $Models) {

        foreach ($seed in $Seeds) {

            $currentRun++

            $header = @"
========================================================================
Milestone 6 Run $currentRun / $ExpectedRemainingRuns
Dataset : medbiot
Fold    : $fold
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
                "--dataset", "medbiot"
                "--split", "ldo"
                "--fold", $fold
                "--random-state", $seed
                "--max-train-rows", $TrainRows
                "--max-test-rows", $TestRows
                "--epochs", $Epochs
                "--batch-size", $BatchSize
                "--output", $ResultsFile
            )

            & python -u @arguments 2>&1 |
                Tee-Object -FilePath $LogFile -Append

            $exitCode = $LASTEXITCODE

            if ($exitCode -ne 0) {

                $message = @"
========================================================================
FAILED
Run       : $currentRun / $ExpectedRemainingRuns
Dataset   : medbiot
Fold      : $fold
Model     : $model
Seed      : $seed
Exit code : $exitCode
========================================================================
"@

                Write-Host $message
                Add-Content $LogFile $message

                throw "Milestone 6 production sweep stopped because this run failed."
            }

            Add-Content $LogFile ""
        }
    }
}

# ---------------------------------------------------------------------------
# Final validation
# ---------------------------------------------------------------------------

if ($currentRun -ne $ExpectedRemainingRuns) {
    throw (
        "Expected $ExpectedRemainingRuns production runs, " +
        "but completed $currentRun."
    )
}

$FinalRows = @(Import-Csv $ResultsFile)

if ($FinalRows.Count -ne $ExpectedFinalRows) {
    throw (
        "Expected $ExpectedFinalRows total CSV rows " +
        "(18 random + 108 LDO), " +
        "but found $($FinalRows.Count)."
    )
}

$FinalRandomRows = @(
    $FinalRows |
        Where-Object {
            $_.split_type -eq "random"
        }
)

$FinalLDORows = @(
    $FinalRows |
        Where-Object {
            $_.split_type -eq "ldo"
        }
)

if ($FinalRandomRows.Count -ne 18) {
    throw (
        "Final validation failed: expected 18 random-split rows, " +
        "found $($FinalRandomRows.Count)."
    )
}

if ($FinalLDORows.Count -ne 108) {
    throw (
        "Final validation failed: expected 108 LDO rows, " +
        "found $($FinalLDORows.Count)."
    )
}

$EndTime = Get-Date

$summary = @"
========================================================================
Milestone 6 LDO production sweep completed successfully
========================================================================
Runs completed      : $currentRun / $ExpectedRemainingRuns
Random baseline     : $($FinalRandomRows.Count) rows
LDO results         : $($FinalLDORows.Count) rows
Total CSV rows      : $($FinalRows.Count)
Started             : $StartTime
Finished            : $EndTime
Results             : $ResultsFile
Log                 : $LogFile
========================================================================
"@

Write-Host $summary
Add-Content $LogFile ""
Add-Content $LogFile $summary