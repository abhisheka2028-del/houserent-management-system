# ==============================================================================
# HouseRent - Module 4: Kubernetes Automation Script (Windows PowerShell)
# ==============================================================================

param (
    [Parameter(Position=0)]
    [ValidateSet("deploy", "status", "scale", "port-forward", "nodeport-url", "rollback", "logs", "clean")]
    [string]$Action = "deploy",

    [Parameter(Position=1)]
    [string]$Param1 = ""
)

$Namespace = "houserent"
$Deployment = "houserent-deployment"

switch ($Action) {
    "deploy" {
        Write-Host "[1/6] Creating Namespace..." -ForegroundColor Cyan
        kubectl apply -f kubernetes/namespace.yaml

        Write-Host "[2/6] Applying ConfigMap..." -ForegroundColor Cyan
        kubectl apply -f kubernetes/configmap.yaml

        Write-Host "[3/6] Applying Secret..." -ForegroundColor Cyan
        if (Test-Path "kubernetes/secret.yaml") {
            kubectl apply -f kubernetes/secret.yaml
        } else {
            Write-Host "[*] Using secret.yaml.example for local evaluation..." -ForegroundColor Yellow
            kubectl apply -f kubernetes/secret.yaml.example
        }

        Write-Host "[4/6] Applying PersistentVolumeClaim..." -ForegroundColor Cyan
        kubectl apply -f kubernetes/pvc.yaml

        Write-Host "[5/6] Deploying Application Pods (Deployment)..." -ForegroundColor Cyan
        kubectl apply -f kubernetes/deployment.yaml

        Write-Host "[6/6] Creating Services (ClusterIP & NodePort)..." -ForegroundColor Cyan
        kubectl apply -f kubernetes/service.yaml

        Write-Host "`n[+] Checking Rollout Status..." -ForegroundColor Green
        kubectl rollout status deployment/$Deployment -n $Namespace --timeout=90s
        kubectl get all -n $Namespace
    }

    "status" {
        Write-Host "=== Pods in namespace '$Namespace' ===" -ForegroundColor Cyan
        kubectl get pods -n $Namespace -o wide
        Write-Host "`n=== PVC in namespace '$Namespace' ===" -ForegroundColor Cyan
        kubectl get pvc -n $Namespace
        Write-Host "`n=== Services in namespace '$Namespace' ===" -ForegroundColor Cyan
        kubectl get svc -n $Namespace
    }

    "scale" {
        $replicas = if ($Param1) { $Param1 } else { "2" }
        Write-Host "[+] Scaling deployment '$Deployment' to $replicas replicas..." -ForegroundColor Cyan
        kubectl scale deployment/$Deployment --replicas=$replicas -n $Namespace
        kubectl rollout status deployment/$Deployment -n $Namespace
        kubectl get pods -n $Namespace
    }

    "port-forward" {
        $port = if ($Param1) { $Param1 } else { "8080" }
        Write-Host "[+] Starting port-forwarding on http://localhost:$port..." -ForegroundColor Green
        Write-Host "    Press Ctrl+C to terminate session."
        kubectl port-forward svc/houserent-service "${port}:80" -n $Namespace
    }

    "nodeport-url" {
        Write-Host "[+] Fetching Minikube NodePort service URL..." -ForegroundColor Cyan
        minikube service houserent-nodeport-service -n $Namespace --url
    }

    "rollback" {
        Write-Host "[!] Rolling back last deployment revision..." -ForegroundColor Yellow
        kubectl rollout undo deployment/$Deployment -n $Namespace
        kubectl rollout status deployment/$Deployment -n $Namespace
    }

    "logs" {
        kubectl logs -l app=houserent -n $Namespace --tail=100 -f
    }

    "clean" {
        Write-Host "[!] Deleting all resources in namespace '$Namespace'..." -ForegroundColor Red
        kubectl delete -f kubernetes/service.yaml
        kubectl delete -f kubernetes/deployment.yaml
        kubectl delete -f kubernetes/pvc.yaml
        kubectl delete -f kubernetes/configmap.yaml
        kubectl delete namespace $Namespace
        Write-Host "[+] Cleanup complete." -ForegroundColor Green
    }
}
