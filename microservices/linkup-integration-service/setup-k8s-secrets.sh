#!/bin/bash
# Setup Kubernetes Secrets for Linkup Integration Service
# This script creates the necessary secrets in your Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Linkup Integration - Kubernetes Secrets${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Configuration
NAMESPACE="clinical-trials"
LINKUP_API_KEY="303d28c4-2d95-456b-9f58-59a0e18cce46"

# Database configuration (update these with your actual values)
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-synthetic_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo -e "${YELLOW}Step 1: Creating namespace (if not exists)${NC}"
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Namespace ready${NC}"
echo ""

echo -e "${YELLOW}Step 2: Creating Linkup API secrets${NC}"
kubectl create secret generic linkup-secrets \
  --from-literal=api-key=${LINKUP_API_KEY} \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Linkup API key secret created${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating database secrets${NC}"
kubectl create secret generic postgres-secrets \
  --from-literal=database-url=${DATABASE_URL} \
  --from-literal=db-host=${DB_HOST} \
  --from-literal=db-port=${DB_PORT} \
  --from-literal=db-name=${DB_NAME} \
  --from-literal=db-user=${DB_USER} \
  --from-literal=db-password=${DB_PASSWORD} \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -
echo -e "${GREEN}✓ Database secrets created${NC}"
echo ""

echo -e "${YELLOW}Step 4: Verifying secrets${NC}"
echo "Secrets in namespace ${NAMESPACE}:"
kubectl get secrets -n ${NAMESPACE} | grep -E "(linkup-secrets|postgres-secrets)"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All secrets configured successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Deploy the service:"
echo "   kubectl apply -f ../../kubernetes/deployments/linkup-integration-service.yaml"
echo ""
echo "2. Deploy the CronJob:"
echo "   kubectl apply -f ../../kubernetes/cronjobs/compliance-watcher.yaml"
echo ""
echo "3. Check service status:"
echo "   kubectl get pods -n ${NAMESPACE} -l app=linkup-integration-service"
echo ""
echo "4. View logs:"
echo "   kubectl logs -f deployment/linkup-integration-service -n ${NAMESPACE}"
echo ""

echo -e "${GREEN}Done!${NC}"
