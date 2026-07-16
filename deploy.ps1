Param (
    [ValidateSet("Link", "Copy", "Install")]
    [string]$Mode,

    [string]$SourceRoot,

    [ValidateSet("CU126", "CU128", "CPU")]
    [string]$Device,

    [ValidateSet("HF", "HF-Mirror", "ModelScope")]
    [string]$ModelSource,

    [switch]$DownloadUVR5,

    [string]$CondaEnvName = "GPTSoVits",

    [ValidateSet("3.10", "3.11", "3.12")]
    [string]$PythonVersion = "3.10",

    [switch]$Force,

    [switch]$RunAfter,

    [switch]$AllowIncompatibleGpuPackage,

    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
}

$script:Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:ConflictPolicy = $null
$script:InitialParameters = @{}
foreach ($key in $PSBoundParameters.Keys) {
    $script:InitialParameters[$key] = $PSBoundParameters[$key]
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Join-RepoPath {
    param([Parameter(Mandatory = $true)][string]$RelativePath)
    return Join-Path $script:Root ($RelativePath -replace "/", "\")
}

function Get-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Assert-UnderRoot {
    param([Parameter(Mandatory = $true)][string]$Path)
    $rootFull = (Get-FullPath $script:Root).TrimEnd("\")
    $pathFull = Get-FullPath $Path
    if ($pathFull -ne $rootFull -and -not $pathFull.StartsWith($rootFull + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "拒绝操作仓库外路径: $pathFull"
    }
}

function Read-RequiredChoice {
    param(
        [Parameter(Mandatory = $true)][string]$Prompt,
        [Parameter(Mandatory = $true)][string[]]$Choices
    )

    while ($true) {
        $value = (Read-Host $Prompt).Trim()
        foreach ($choice in $Choices) {
            if ($value.Equals($choice, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $choice
            }
        }
        Write-Warn "请输入: $($Choices -join ', ')。直接回车不会选择默认项。"
    }
}

function Select-DeployMode {
    Write-Host ""
    Write-Host "请选择部署模式:"
    Write-Host "  1) 软链接复用已有 GPT-SoVITS 示例目录"
    Write-Host "  2) 复制已有 GPT-SoVITS 示例目录资源"
    Write-Host "  3) 全新 conda 环境安装"
    $choice = Read-RequiredChoice -Prompt "输入 1/2/3" -Choices @("1", "2", "3")
    switch ($choice) {
        "1" { return "Link" }
        "2" { return "Copy" }
        "3" { return "Install" }
    }
}

function Select-Device {
    Write-Host ""
    Write-Host "请选择 PyTorch 设备包:"
    Write-Host "  1) CU128 - NVIDIA CUDA 12.8"
    Write-Host "  2) CU126 - NVIDIA CUDA 12.6"
    Write-Host "  3) CPU   - 无 CUDA 或仅 CPU"
    $choice = Read-RequiredChoice -Prompt "输入 1/2/3" -Choices @("1", "2", "3")
    switch ($choice) {
        "1" { return "CU128" }
        "2" { return "CU126" }
        "3" { return "CPU" }
    }
}

function Select-ModelSource {
    Write-Host ""
    Write-Host "请选择模型下载源:"
    Write-Host "  1) HF - HuggingFace"
    Write-Host "  2) HF-Mirror - HuggingFace 镜像"
    Write-Host "  3) ModelScope"
    $choice = Read-RequiredChoice -Prompt "输入 1/2/3" -Choices @("1", "2", "3")
    switch ($choice) {
        "1" { return "HF" }
        "2" { return "HF-Mirror" }
        "3" { return "ModelScope" }
    }
}

function Select-YesNo {
    param([Parameter(Mandatory = $true)][string]$Prompt)
    $choice = Read-RequiredChoice -Prompt "$Prompt [Y/N]" -Choices @("Y", "N")
    return $choice -eq "Y"
}

function Get-ReusableEntries {
    $dirs = @(
        "runtime",
        "py312",
        ".venv",
        "GPT_SoVITS/pretrained_models",
        "GPT_SoVITS/text/G2PWModel",
        "tools/uvr5/uvr5_weights",
        "tools/asr/models",
        "tools/denoise-model",
        "tools/AP_BWE_main/24kto48k",
        "GPT_weights",
        "GPT_weights_v2",
        "GPT_weights_v3",
        "GPT_weights_v4",
        "GPT_weights_v2Pro",
        "GPT_weights_v2ProPlus",
        "SoVITS_weights",
        "SoVITS_weights_v2",
        "SoVITS_weights_v3",
        "SoVITS_weights_v4",
        "SoVITS_weights_v2Pro",
        "SoVITS_weights_v2ProPlus",
        "logs",
        "output",
        "ref_audios"
    )

    $files = @(
        "weight.json",
        "cfg.json",
        "speakers.json"
    )

    $entries = @()
    foreach ($dir in $dirs) {
        $entries += [PSCustomObject]@{ RelativePath = $dir; Kind = "Directory" }
    }
    foreach ($file in $files) {
        $entries += [PSCustomObject]@{ RelativePath = $file; Kind = "File" }
    }
    return $entries
}

function Get-AlwaysCreateDirectories {
    return @(
        "GPT_weights",
        "GPT_weights_v2",
        "GPT_weights_v3",
        "GPT_weights_v4",
        "GPT_weights_v2Pro",
        "GPT_weights_v2ProPlus",
        "SoVITS_weights",
        "SoVITS_weights_v2",
        "SoVITS_weights_v3",
        "SoVITS_weights_v4",
        "SoVITS_weights_v2Pro",
        "SoVITS_weights_v2ProPlus",
        "logs",
        "output"
    )
}

function Get-SourcePath {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$RelativePath
    )
    return Join-Path $Root ($RelativePath -replace "/", "\")
}

function Resolve-SourceRoot {
    param([string]$Path)

    while ([string]::IsNullOrWhiteSpace($Path)) {
        $Path = Read-Host "请输入已有 GPT-SoVITS 示例目录完整路径"
    }

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "源目录不存在: $Path"
    }

    $resolved = (Resolve-Path -LiteralPath $Path).ProviderPath
    $sourceFull = (Get-FullPath $resolved).TrimEnd("\")
    $rootFull = (Get-FullPath $script:Root).TrimEnd("\")
    if ($sourceFull.Equals($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "源目录不能是当前仓库自身。"
    }

    $hasWebUi = Test-Path -LiteralPath (Join-Path $resolved "webui.py")
    $hasPackageDir = Test-Path -LiteralPath (Join-Path $resolved "GPT_SoVITS")
    if (-not ($hasWebUi -and $hasPackageDir)) {
        throw "源目录不像 GPT-SoVITS 根目录，缺少 webui.py 或 GPT_SoVITS。"
    }

    return $resolved
}

function Ensure-ParentDirectory {
    param([Parameter(Mandatory = $true)][string]$Path)
    $parent = Split-Path -Parent $Path
    if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
        Assert-UnderRoot $parent
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
}

function Get-ReparseTargets {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return @()
    }

    $item = Get-Item -LiteralPath $Path -Force
    if (-not ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        return @()
    }

    if ($null -eq $item.Target) {
        return @()
    }

    return @($item.Target)
}

function Test-AlreadyLinked {
    param(
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$SourcePath
    )

    $sourceFull = (Get-FullPath $SourcePath).TrimEnd("\")
    foreach ($target in (Get-ReparseTargets -Path $TargetPath)) {
        $targetFull = (Get-FullPath $target).TrimEnd("\")
        if ($targetFull.Equals($sourceFull, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Select-ConflictPolicy {
    if ($Force) {
        return "R"
    }

    if ($null -ne $script:ConflictPolicy) {
        return $script:ConflictPolicy
    }

    Write-Host ""
    Write-Warn "目标路径已存在。请选择本次部署的统一处理方式:"
    Write-Host "  S) 跳过已有目标"
    Write-Host "  R) 删除已有目标后替换"
    Write-Host "  B) 备份已有目标后替换"
    Write-Host "  A) 中止部署"
    $script:ConflictPolicy = Read-RequiredChoice -Prompt "输入 S/R/B/A" -Choices @("S", "R", "B", "A")
    return $script:ConflictPolicy
}

function Remove-TargetForDeploy {
    param([Parameter(Mandatory = $true)][string]$TargetPath)
    Assert-UnderRoot $TargetPath

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        return
    }

    $item = Get-Item -LiteralPath $TargetPath -Force
    if ($item.PSIsContainer -and ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        Remove-Item -LiteralPath $TargetPath -Force
    } else {
        Remove-Item -LiteralPath $TargetPath -Recurse -Force
    }
}

function Backup-TargetForDeploy {
    param([Parameter(Mandatory = $true)][string]$TargetPath)
    Assert-UnderRoot $TargetPath

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "$TargetPath.backup-$stamp"
    Assert-UnderRoot $backupPath
    Move-Item -LiteralPath $TargetPath -Destination $backupPath
    Write-Info "已备份: $TargetPath -> $backupPath"
}

function Prepare-Target {
    param(
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$SourcePath
    )

    Assert-UnderRoot $TargetPath

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        return $true
    }

    if (Test-AlreadyLinked -TargetPath $TargetPath -SourcePath $SourcePath) {
        Write-Info "已链接，跳过: $TargetPath"
        return $false
    }

    $policy = Select-ConflictPolicy
    switch ($policy) {
        "S" {
            Write-Info "跳过已有目标: $TargetPath"
            return $false
        }
        "R" {
            Remove-TargetForDeploy -TargetPath $TargetPath
            return $true
        }
        "B" {
            Backup-TargetForDeploy -TargetPath $TargetPath
            return $true
        }
        "A" {
            throw "用户中止部署。"
        }
    }
}

function New-JunctionLink {
    param(
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$SourcePath
    )

    Ensure-ParentDirectory -Path $TargetPath
    New-Item -ItemType Junction -Path $TargetPath -Target $SourcePath | Out-Null
}

function Copy-ReusableEntry {
    param(
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$Kind
    )

    Ensure-ParentDirectory -Path $TargetPath
    if ($Kind -eq "Directory") {
        Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Recurse -Force
    } else {
        Copy-Item -LiteralPath $SourcePath -Destination $TargetPath -Force
    }
}

function Invoke-ReuseDeployment {
    param(
        [Parameter(Mandatory = $true)][ValidateSet("Link", "Copy")][string]$DeploymentMode,
        [Parameter(Mandatory = $true)][string]$ResolvedSourceRoot
    )

    $entries = Get-ReusableEntries
    $applied = 0
    $missing = 0

    foreach ($entry in $entries) {
        $sourcePath = Get-SourcePath -Root $ResolvedSourceRoot -RelativePath $entry.RelativePath
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            $missing += 1
            continue
        }

        $targetPath = Join-RepoPath $entry.RelativePath
        if (-not (Prepare-Target -TargetPath $targetPath -SourcePath $sourcePath)) {
            continue
        }

        if ($DeploymentMode -eq "Link" -and $entry.Kind -eq "Directory") {
            New-JunctionLink -TargetPath $targetPath -SourcePath $sourcePath
            Write-Info "已创建目录链接: $($entry.RelativePath)"
        } else {
            Copy-ReusableEntry -TargetPath $targetPath -SourcePath $sourcePath -Kind $entry.Kind
            if ($DeploymentMode -eq "Link") {
                Write-Info "已复制小型配置文件: $($entry.RelativePath)"
            } else {
                Write-Info "已复制: $($entry.RelativePath)"
            }
        }
        $applied += 1
    }

    Initialize-LocalDirectories
    Clear-DeployEnvBatch

    Write-Ok "资源复用完成，处理 $applied 项，源目录缺失 $missing 项。"
    $python = Get-FirstPythonCandidate -Root $script:Root
    if ($null -eq $python) {
        Write-Warn "当前仓库尚未找到 runtime、py312 或 .venv Python。若源目录没有可复用环境，请再运行全新安装模式。"
    } else {
        Write-Ok "发现 Python: $python"
        Assert-ReusedPythonGpuCompatible -PythonPath $python
    }
}

function Initialize-LocalDirectories {
    foreach ($relativePath in (Get-AlwaysCreateDirectories)) {
        $targetPath = Join-RepoPath $relativePath
        if (-not (Test-Path -LiteralPath $targetPath)) {
            Assert-UnderRoot $targetPath
            New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
        }
    }
}

function Get-PythonCandidates {
    param([Parameter(Mandatory = $true)][string]$Root)
    return @(
        (Join-Path $Root "runtime\python.exe"),
        (Join-Path $Root "py312\python.exe"),
        (Join-Path $Root ".venv\Scripts\python.exe")
    )
}

function Get-FirstPythonCandidate {
    param([Parameter(Mandatory = $true)][string]$Root)
    foreach ($candidate in (Get-PythonCandidates -Root $Root)) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

function Get-CondaCommand {
    $cmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        throw "未找到 conda。请先安装 Miniforge/Anaconda，并确保 conda 在 PATH 中。"
    }
    return $cmd.Source
}

function Convert-VersionText {
    param([string]$VersionText)
    if ([string]::IsNullOrWhiteSpace($VersionText)) {
        return $null
    }

    try {
        return [version]$VersionText
    } catch {
        return $null
    }
}

function Test-BlackwellGpuName {
    param([string]$Name)
    if ([string]::IsNullOrWhiteSpace($Name)) {
        return $false
    }

    return $Name -match "(?i)\bRTX\s*(PRO\s*)?50\d{2}\b" -or
        $Name -match "(?i)\bGeForce\s+RTX\s*50" -or
        $Name -match "(?i)\bBlackwell\b" -or
        $Name -match "(?i)\bGB10\b"
}

function Test-BlackwellComputeCapability {
    param([string]$ComputeCapability)
    $version = Convert-VersionText $ComputeCapability
    return $null -ne $version -and $version.Major -ge 12
}

function Get-WindowsNvidiaGpuInfo {
    $controllers = @()
    try {
        $controllers = @(Get-CimInstance -ClassName Win32_VideoController -ErrorAction Stop)
    } catch {
        return [PSCustomObject]@{
            Available = $false
            Gpus = @()
            DriverCudaVersion = $null
        }
    }

    $gpus = @($controllers | Where-Object {
        ([string]$_.AdapterCompatibility -match "(?i)NVIDIA") -or
        ([string]$_.Name -match "(?i)NVIDIA") -or
        ([string]$_.PNPDeviceID -match "(?i)VEN_10DE")
    } | ForEach-Object {
        [PSCustomObject]@{
            Name = ([string]$_.Name).Trim()
            ComputeCapability = ""
            DriverVersion = ([string]$_.DriverVersion).Trim()
        }
    })

    return [PSCustomObject]@{
        Available = @($gpus).Count -gt 0
        Gpus = @($gpus)
        DriverCudaVersion = $null
    }
}

function Test-RequiresCu128 {
    param([Parameter(Mandatory = $true)]$GpuInfo)
    foreach ($gpu in @($GpuInfo.Gpus)) {
        if ((Test-BlackwellGpuName -Name $gpu.Name) -or (Test-BlackwellComputeCapability -ComputeCapability $gpu.ComputeCapability)) {
            return $true
        }
    }
    return $false
}

function Test-TorchCudaSupportsCu128 {
    param([string]$TorchCudaVersion)
    $version = Convert-VersionText $TorchCudaVersion
    return $null -ne $version -and $version -ge ([version]"12.8")
}

function Get-TorchCudaVersion {
    param([Parameter(Mandatory = $true)][string]$PythonPath)

    if (-not (Test-Path -LiteralPath $PythonPath)) {
        return $null
    }

    $code = "import torch; print(torch.version.cuda or '')"
    $output = & $PythonPath -c $code 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    return (($output | Select-Object -First 1) -as [string]).Trim()
}

function Assert-GpuPackageCompatible {
    param(
        [Parameter(Mandatory = $true)][string]$SelectedDevice,
        $GpuInfo = (Get-WindowsNvidiaGpuInfo)
    )

    if ($SelectedDevice -eq "CPU") {
        return
    }

    if (-not $GpuInfo.Available -or @($GpuInfo.Gpus).Count -eq 0) {
        Write-Warn "未通过 Windows 显卡信息检测到 NVIDIA GPU，无法自动校验 NVIDIA 代际兼容性。"
        return
    }

    $gpuSummary = (@($GpuInfo.Gpus) | ForEach-Object {
        if ([string]::IsNullOrWhiteSpace($_.ComputeCapability)) {
            $_.Name
        } else {
            "$($_.Name) (SM $($_.ComputeCapability))"
        }
    }) -join "; "
    Write-Info "检测到 NVIDIA GPU: $gpuSummary"

    if (Test-RequiresCu128 -GpuInfo $GpuInfo) {
        if ($SelectedDevice -ne "CU128" -and -not $AllowIncompatibleGpuPackage) {
            throw "检测到 RTX 50/Blackwell 代际 GPU，请选择 CU128。使用 CU126 常见结果是 PyTorch CUDA kernel 不兼容或无法运行。"
        }

        $driverCuda = Convert-VersionText $GpuInfo.DriverCudaVersion
        if ($null -ne $driverCuda -and $driverCuda -lt ([version]"12.8")) {
            Write-Warn "已检测到的驱动 CUDA 能力为 $($GpuInfo.DriverCudaVersion)，低于 12.8。RTX 50/Blackwell 建议先升级 NVIDIA 驱动。"
        }

        if ($SelectedDevice -eq "CU128") {
            Write-Ok "RTX 50/Blackwell 已选择 CU128，避开 cu126 兼容坑。"
        }
    }
}

function Assert-ReusedPythonGpuCompatible {
    param(
        [string]$PythonPath,
        $GpuInfo = (Get-WindowsNvidiaGpuInfo)
    )

    if ([string]::IsNullOrWhiteSpace($PythonPath)) {
        return
    }

    if (-not (Test-RequiresCu128 -GpuInfo $GpuInfo)) {
        return
    }

    $torchCuda = Get-TorchCudaVersion -PythonPath $PythonPath
    if ([string]::IsNullOrWhiteSpace($torchCuda)) {
        Write-Warn "检测到 RTX 50/Blackwell，但无法读取复用 Python 中的 torch.version.cuda。若启动失败，请用全新安装模式选择 CU128。"
        return
    }

    if (-not (Test-TorchCudaSupportsCu128 -TorchCudaVersion $torchCuda) -and -not $AllowIncompatibleGpuPackage) {
        throw "检测到 RTX 50/Blackwell，但复用 Python 的 PyTorch CUDA 是 $torchCuda。请改用全新安装模式选择 CU128，或复用已安装 cu128 PyTorch 的环境。"
    }

    Write-Ok "复用 Python 的 PyTorch CUDA 为 $torchCuda，满足 RTX 50/Blackwell 的 CU128 要求。"
}

function Test-CondaEnvExists {
    param([Parameter(Mandatory = $true)][string]$EnvName)
    $jsonText = (& conda env list --json) -join "`n"
    if ($LASTEXITCODE -ne 0) {
        throw "无法读取 conda 环境列表。"
    }
    $envInfo = $jsonText | ConvertFrom-Json
    foreach ($envPath in $envInfo.envs) {
        if ((Split-Path $envPath -Leaf).Equals($EnvName, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    Write-Info "运行: $FilePath $($Arguments -join ' ')"
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "命令失败，退出码: $LASTEXITCODE"
    }
}

function Assert-InstalledTorchDeviceCompatible {
    param(
        [Parameter(Mandatory = $true)][string]$EnvName,
        [Parameter(Mandatory = $true)][ValidateSet("CU126", "CU128", "CPU")][string]$SelectedDevice
    )

    $expectedCuda = switch ($SelectedDevice) {
        "CU128" { "12.8" }
        "CU126" { "12.6" }
        "CPU" { $null }
    }
    if ($SelectedDevice -eq "CPU") {
        $code = "import torch; assert torch.version.cuda is None, f'expected CPU-only Torch, got CUDA {torch.version.cuda}'; print('Torch CPU probe OK')"
    } else {
        $code = "import torch; assert torch.cuda.is_available(), 'CUDA is unavailable'; runtime = str(torch.version.cuda or ''); assert runtime.startswith('$expectedCuda'), f'expected CUDA $expectedCuda, got {runtime}'; print(torch.cuda.get_device_name(0))"
    }

    Invoke-CheckedCommand -FilePath "conda" -Arguments @("run", "-n", $EnvName, "python", "-c", $code)
    Write-Ok "安装后 PyTorch $SelectedDevice 探针通过。"
}

function New-DeployEnvBatch {
    param([Parameter(Mandatory = $true)][string]$EnvName)
    $path = Join-RepoPath "deploy.env.bat"
    Assert-UnderRoot $path
    $content = @(
        "@echo off",
        "set `"GPTSOVITS_CONDA_ENV=$EnvName`""
    )
    Set-Content -LiteralPath $path -Value $content -Encoding ASCII
}

function Clear-DeployEnvBatch {
    $path = Join-RepoPath "deploy.env.bat"
    if (Test-Path -LiteralPath $path) {
        Remove-TargetForDeploy -TargetPath $path
    }
}

function Invoke-FreshInstall {
    if ([string]::IsNullOrWhiteSpace($Device)) {
        $script:Device = Select-Device
    }
    if ([string]::IsNullOrWhiteSpace($ModelSource)) {
        $script:ModelSource = Select-ModelSource
    }

    $downloadUvr5Requested = $DownloadUVR5
    if (-not $script:InitialParameters.ContainsKey("DownloadUVR5")) {
        $downloadUvr5Requested = Select-YesNo -Prompt "是否下载 UVR5 模型"
    }

    Assert-GpuPackageCompatible -SelectedDevice $Device

    Get-CondaCommand | Out-Null

    if (Test-CondaEnvExists -EnvName $CondaEnvName) {
        Write-Warn "conda 环境已存在: $CondaEnvName"
        if (-not $Force) {
            $reuse = Select-YesNo -Prompt "是否复用该环境继续安装/修复依赖"
            if (-not $reuse) {
                throw "用户取消复用已有 conda 环境。"
            }
        }
    } else {
        Invoke-CheckedCommand -FilePath "conda" -Arguments @("create", "-y", "-n", $CondaEnvName, "python=$PythonVersion")
    }

    $installScript = Join-RepoPath "install.ps1"
    $installArgs = @(
        "run",
        "-n",
        $CondaEnvName,
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $installScript,
        "-Device",
        $Device,
        "-Source",
        $ModelSource
    )
    if ($downloadUvr5Requested) {
        $installArgs += "-DownloadUVR5"
    }

    Invoke-CheckedCommand -FilePath "conda" -Arguments $installArgs
    Assert-InstalledTorchDeviceCompatible -EnvName $CondaEnvName -SelectedDevice $Device
    Initialize-LocalDirectories
    New-DeployEnvBatch -EnvName $CondaEnvName
    Write-Ok "全新安装完成，启动脚本将使用 conda 环境: $CondaEnvName"
}

function Show-NextSteps {
    Write-Host ""
    Write-Ok "部署步骤已完成。"
    Write-Host "启动 WebUI: 双击 go-webui.bat"
    Write-Host "重新部署: 双击 deploy.bat"

    if (-not $script:InitialParameters.ContainsKey("RunAfter")) {
        $startNow = Select-YesNo -Prompt "是否现在启动 WebUI"
        if ($startNow) {
            & (Join-RepoPath "go-webui.bat")
        }
    } elseif ($RunAfter) {
        & (Join-RepoPath "go-webui.bat")
    }
}

function Invoke-Main {
    Set-Location $script:Root
    Write-Host ""
    Write-Host "GPT-SoVITS 一键部署"
    Write-Host "仓库: $script:Root"

    if ([string]::IsNullOrWhiteSpace($Mode)) {
        $script:Mode = Select-DeployMode
    }

    switch ($Mode) {
        "Link" {
            $resolvedSource = Resolve-SourceRoot -Path $SourceRoot
            Invoke-ReuseDeployment -DeploymentMode "Link" -ResolvedSourceRoot $resolvedSource
        }
        "Copy" {
            $resolvedSource = Resolve-SourceRoot -Path $SourceRoot
            Invoke-ReuseDeployment -DeploymentMode "Copy" -ResolvedSourceRoot $resolvedSource
        }
        "Install" {
            Invoke-FreshInstall
        }
    }

    Show-NextSteps
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) {
        throw "SelfTest failed: $Message"
    }
}

function Invoke-SelfTest {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("gsv-deploy-test-" + [System.Guid]::NewGuid().ToString("N"))
    $source = Join-Path $tempRoot "source"
    $target = Join-Path $tempRoot "target"
    $oldRoot = $script:Root

    try {
        New-Item -ItemType Directory -Path $source -Force | Out-Null
        New-Item -ItemType Directory -Path $target -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $source "GPT_SoVITS") -Force | Out-Null
        New-Item -ItemType File -Path (Join-Path $source "webui.py") -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $source "py312") -Force | Out-Null
        New-Item -ItemType File -Path (Join-Path $source "py312\python.exe") -Force | Out-Null

        $script:Root = $target

        $resolvedSource = Resolve-SourceRoot -Path $source
        Assert-True -Condition ((Get-FullPath $resolvedSource).TrimEnd("\").Equals((Get-FullPath $source).TrimEnd("\"), [System.StringComparison]::OrdinalIgnoreCase)) -Message "Resolve-SourceRoot should resolve source path"

        $entries = Get-ReusableEntries
        Assert-True -Condition (@($entries | Where-Object { $_.RelativePath -eq "GPT_SoVITS/pretrained_models" }).Count -eq 1) -Message "Reusable entries should include pretrained models"
        Assert-True -Condition (@($entries | Where-Object { $_.RelativePath -eq "SoVITS_weights_v2ProPlus" }).Count -eq 1) -Message "Reusable entries should include v2ProPlus SoVITS weights"

        $python = Get-FirstPythonCandidate -Root $source
        Assert-True -Condition ($python.EndsWith("py312\python.exe", [System.StringComparison]::OrdinalIgnoreCase)) -Message "Python candidate should find py312"

        New-DeployEnvBatch -EnvName "UnitEnv"
        $envPath = Join-Path $target "deploy.env.bat"
        Assert-True -Condition (Test-Path -LiteralPath $envPath) -Message "deploy.env.bat should be written"
        $envText = Get-Content -LiteralPath $envPath -Raw
        Assert-True -Condition ($envText.Contains('set "GPTSOVITS_CONDA_ENV=UnitEnv"')) -Message "deploy.env.bat should contain env name"

        $rtx50Info = [PSCustomObject]@{
            Available = $true
            Gpus = @([PSCustomObject]@{ Name = "NVIDIA GeForce RTX 5090"; ComputeCapability = "12.0" })
            DriverCudaVersion = "12.8"
        }
        Assert-True -Condition (Test-RequiresCu128 -GpuInfo $rtx50Info) -Message "RTX 50 series should require CU128"
        Assert-True -Condition (-not (Test-TorchCudaSupportsCu128 -TorchCudaVersion "12.6")) -Message "Torch CUDA 12.6 should not satisfy RTX 50 requirements"
        Assert-True -Condition (Test-TorchCudaSupportsCu128 -TorchCudaVersion "12.8") -Message "Torch CUDA 12.8 should satisfy RTX 50 requirements"
        Assert-True -Condition (Test-TorchCudaSupportsCu128 -TorchCudaVersion "13.0") -Message "Torch CUDA 13.0 should satisfy RTX 50 requirements"
        $blockedCu126 = $false
        try {
            Assert-GpuPackageCompatible -SelectedDevice "CU126" -GpuInfo $rtx50Info
        } catch {
            $blockedCu126 = $true
        }
        Assert-True -Condition $blockedCu126 -Message "RTX 50 series should block CU126"
        Assert-GpuPackageCompatible -SelectedDevice "CU128" -GpuInfo $rtx50Info
        Assert-GpuPackageCompatible -SelectedDevice "CPU" -GpuInfo $rtx50Info

        $legacyInfo = [PSCustomObject]@{
            Available = $true
            Gpus = @([PSCustomObject]@{ Name = "NVIDIA GeForce RTX 4090"; ComputeCapability = "8.9" })
            DriverCudaVersion = "12.8"
        }
        Assert-True -Condition (-not (Test-RequiresCu128 -GpuInfo $legacyInfo)) -Message "RTX 4090 should not be forced to CU128"
        Assert-GpuPackageCompatible -SelectedDevice "CU126" -GpuInfo $legacyInfo

        $rtx6000AdaInfo = [PSCustomObject]@{
            Available = $true
            Gpus = @([PSCustomObject]@{ Name = "NVIDIA RTX 6000 Ada Generation"; ComputeCapability = "8.9" })
            DriverCudaVersion = "12.8"
        }
        Assert-True -Condition (-not (Test-RequiresCu128 -GpuInfo $rtx6000AdaInfo)) -Message "RTX 6000 Ada should not be forced to CU128 by name"

        $rtxProBlackwellInfo = [PSCustomObject]@{
            Available = $true
            Gpus = @([PSCustomObject]@{ Name = "NVIDIA RTX PRO 6000 Blackwell Server Edition"; ComputeCapability = "12.0" })
            DriverCudaVersion = "12.8"
        }
        Assert-True -Condition (Test-RequiresCu128 -GpuInfo $rtxProBlackwellInfo) -Message "RTX PRO Blackwell should require CU128"

        Assert-UnderRoot -Path (Join-Path $target "logs")
        $blocked = $false
        try {
            Assert-UnderRoot -Path $source
        } catch {
            $blocked = $true
        }
        Assert-True -Condition $blocked -Message "Assert-UnderRoot should block paths outside target root"

        Write-Ok "SelfTest passed"
    } finally {
        $script:Root = $oldRoot
        if (Test-Path -LiteralPath $tempRoot) {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force
        }
    }
}

try {
    if ($SelfTest) {
        Invoke-SelfTest
        exit 0
    }

    Invoke-Main
} catch {
    Write-Fail $_.Exception.Message
    exit 1
}
