param(
    [ValidateSet("Codex", "Claude", "Both")]
    [string]$Target = "Both"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$source = Join-Path $repoRoot ".claude\skills"
$obsoleteSkills = @(
    "posit-plotnine-evals"
)

if (-not (Test-Path $source)) {
    throw "No project skills found at $source"
}

function Copy-SkillsTo {
    param(
        [string]$Destination
    )

    New-Item -ItemType Directory -Force -Path $Destination | Out-Null

    foreach ($skillName in $obsoleteSkills) {
        $obsoletePath = Join-Path $Destination $skillName
        if (Test-Path $obsoletePath) {
            Remove-Item -LiteralPath $obsoletePath -Recurse -Force
            Write-Host "Removed obsolete skill $skillName from $Destination"
        }
    }

    Get-ChildItem -Path $source -Directory | ForEach-Object {
        $targetPath = Join-Path $Destination $_.Name
        if (Test-Path $targetPath) {
            Remove-Item -LiteralPath $targetPath -Recurse -Force
        }
        Copy-Item -LiteralPath $_.FullName -Destination $targetPath -Recurse
        Write-Host "Installed $($_.Name) -> $targetPath"
    }
}

if ($Target -eq "Codex" -or $Target -eq "Both") {
    Copy-SkillsTo -Destination (Join-Path $HOME ".codex\skills")
}

if ($Target -eq "Claude" -or $Target -eq "Both") {
    Copy-SkillsTo -Destination (Join-Path $HOME ".claude\skills")
}

Write-Host "Done. Restart Claude Code or Codex so newly installed skills are discovered."
