#!/usr/bin/env bash
# ==============================================================================
# HouseRent - Module 4: Kubernetes Automation Script (Linux / macOS)
# ==============================================================================

set -euo pipefail

NAMESPACE="houserent"
DEPLOYMENT="houserent-deployment"
ACTION="${1:-deploy}"
PARAM1="${2:-}"

case "$ACTION" in
    deploy)
        echo "[1/6] Creating Namespace..."
        kubectl apply -f kubernetes/namespace.yaml

        echo "[2/6] Applying ConfigMap..."
        kubectl apply -f kubernetes/configmap.yaml

        echo "[3/6] Applying Secret..."
        if [ -f "kubernetes/secret.yaml" ]; then
            kubectl apply -f kubernetes/secret.yaml
        else
            echo "[*] Using secret.yaml.example for local evaluation..."
            kubectl apply -f kubernetes/secret.yaml.example
        fi

        echo "[4/6] Applying PersistentVolumeClaim..."
        kubectl apply -f kubernetes/pvc.yaml

        echo "[5/6] Deploying Application Pods (Deployment)..."
        kubectl apply -f kubernetes/deployment.yaml

        echo "[6/6] Creating Services (ClusterIP & NodePort)..."
        kubectl apply -f kubernetes/service.yaml

        echo -e "\n[+] Checking Rollout Status..."
        kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=90s
        kubectl get all -n "$NAMESPACE"
        ;;

    status)
        echo "=== Pods in namespace '$NAMESPACE' ==="
        kubectl get pods -n "$NAMESPACE" -o wide
        echo -e "\n=== PVC in namespace '$NAMESPACE' ==="
        kubectl get pvc -n "$NAMESPACE"
        echo -e "\n=== Services in namespace '$NAMESPACE' ==="
        kubectl get svc -n "$NAMESPACE"
        ;;

    scale)
        REPLICAS="${PARAM1:-2}"
        echo "[+] Scaling deployment '$DEPLOYMENT' to $REPLICAS replicas..."
        kubectl scale deployment/"$DEPLOYMENT" --replicas="$REPLICAS" -n "$NAMESPACE"
        kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE"
        kubectl get pods -n "$NAMESPACE"
        ;;

    port-forward)
        PORT="${PARAM1:-8080}"
        echo "[+] Starting port-forwarding on http://localhost:$PORT..."
        kubectl port-forward svc/houserent-service "$PORT:80" -n "$NAMESPACE"
        ;;

    nodeport-url)
        echo "[+] Fetching Minikube NodePort service URL..."
        minikube service houserent-nodeport-service -n "$NAMESPACE" --url
        ;;

    rollback)
        echo "[!] Rolling back last deployment revision..."
        kubectl rollout undo deployment/"$DEPLOYMENT" -n "$NAMESPACE"
        kubectl rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE"
        ;;

    logs)
        kubectl logs -l app=houserent -n "$NAMESPACE" --tail=100 -f
        ;;

    clean)
        echo "[!] Deleting all resources in namespace '$NAMESPACE'..."
        kubectl delete -f kubernetes/service.yaml --ignore-not-found
        kubectl delete -f kubernetes/deployment.yaml --ignore-not-found
        kubectl delete -f kubernetes/pvc.yaml --ignore-not-found
        kubectl delete -f kubernetes/configmap.yaml --ignore-not-found
        kubectl delete namespace "$NAMESPACE" --ignore-not-found
        echo "[+] Cleanup complete."
        ;;

    *)
        echo "Usage: $0 {deploy|status|scale [n]|port-forward [port]|nodeport-url|rollback|logs|clean}"
        exit 1
        ;;
esac
