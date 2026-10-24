# ==============================================================================
# HouseRent - Module 3: Docker Automation Script (Windows PowerShell)
# ==============================================================================

param (
    [Parameter(Position=0)]
    [ValidateSet("build", "run", "compose", "logs", "stop", "clean", "tag-push")]
    [string]$Action = "run",

    [Parameter(Position=1)]
    [string]$DockerUser = ""
)

$ImageName = "houserent:v1.0"
$ContainerName = "houserent-app"
$Port = "5000"

switch ($Action) {
    "build" {
        Write-Host "[+] Building Docker image '$ImageName'..." -ForegroundColor Cyan
        docker build -t $ImageName .
        Write-Host "[+] Build complete." -ForegroundColor Green
    }

    "run" {
        Write-Host "[+] Ensuring data directory exists for persistent SQLite..." -ForegroundColor Cyan
        if (-not (Test-Path ".\data")) {
            New-Item -ItemType Directory -Path ".\data" | Out-Null
        }

        $existing = docker ps -a -q -f "name=$ContainerName"
        if ($existing) {
            Write-Host "[!] Container $ContainerName already exists. Removing older instance..." -ForegroundColor Yellow
            docker rm -f $ContainerName | Out-Null
        }

        $dataVolume = "$((Get-Item .).FullName)\data:/app/data"
        Write-Host "[+] Starting container '$ContainerName' on http://localhost:$Port..." -ForegroundColor Cyan
        docker run -d `
            --name $ContainerName `
            -p "${Port}:5000" `
            -v "$dataVolume" `
            -e FLASK_ENV=production `
            -e SECRET_KEY="docker-run-secure-key-2026" `
            -e DATABASE_PATH="/app/data/houserent.db" `
            -e UPLOAD_FOLDER="/app/data/uploads" `
            $ImageName

        Start-Sleep -Seconds 3
        docker ps --filter "name=$ContainerName"
        Write-Host "`n[+] Access HouseRent website at: http://localhost:$Port" -ForegroundColor Green
    }

    "compose" {
        Write-Host "[+] Running docker compose up -d --build..." -ForegroundColor Cyan
        docker compose up -d --build
        docker compose ps
    }

    "logs" {
        docker logs -f $ContainerName
    }

    "stop" {
        Write-Host "[*] Stopping container '$ContainerName'..." -ForegroundColor Yellow
        docker stop $ContainerName
    }

    "clean" {
        Write-Host "[!] Removing container '$ContainerName'..." -ForegroundColor Red
        docker rm -f $ContainerName
    }

    "tag-push" {
        if (-not $DockerUser) {
            Write-Error "Please specify Docker Hub username. Example: .\scripts\run_docker.ps1 tag-push yourusername"
            return
        }
        $HubTag = "${DockerUser}/houserent:v1.0"
        Write-Host "[+] Tagging image as '$HubTag'..." -ForegroundColor Cyan
        docker tag $ImageName $HubTag
        Write-Host "[+] Pushing image to Docker Hub..." -ForegroundColor Cyan
        docker push $HubTag
    }
}
