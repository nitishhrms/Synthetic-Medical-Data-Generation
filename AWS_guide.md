# Kubernetes and AWS Integration Plan
## Synthetic Medical Data Generation Platform

---

## Executive Summary

This plan outlines a comprehensive strategy to enhance the existing Kubernetes and AWS infrastructure for the **SyntheticTrialStudio Enterprise Platform**. The project already has foundational Kubernetes manifests and Terraform configurations, but requires significant enhancements for production-grade deployment on AWS with full orchestration capabilities.

---

## Current State Analysis

### ✅ What Already Exists

#### Infrastructure
- ✅ Basic Terraform configuration for AWS (VPC, RDS PostgreSQL, ElastiCache Redis, S3)
- ✅ Kubernetes deployment manifests for 7 microservices
- ✅ Horizontal Pod Autoscaler (HPA) configurations
- ✅ Docker Compose setup for local development
- ✅ Dockerfiles for all microservices

#### Microservices Architecture
- **API Gateway** (Port 8000) - Central routing, rate limiting
- **EDC Service** (Port 8001) - Electronic Data Capture
- **Data Generation Service** (Port 8002) - Synthetic data generation (6+ algorithms)
- **Analytics Service** (Port 8003) - Statistics & reporting
- **Quality Service** (Port 8004) - Edit checks & validation
- **Security Service** (Port 8005) - JWT auth, PHI encryption
- **Daft Analytics Service** (Port 8007) - Distributed data analysis

#### Supporting Infrastructure
- PostgreSQL database for persistence
- Redis for caching and session management
- Frontend (React/Next.js on port 3000)

---

### ❌ What's Missing for Production AWS + Kubernetes

#### Critical Gaps

**1. No EKS (Elastic Kubernetes Service) Configuration**
- Current Kubernetes manifests assume local Minikube
- No EKS cluster Terraform module
- No node groups or managed node configuration

**2. Incomplete Kubernetes Resources**
- No Ingress controller for external access
- No persistent volume claims for stateful services
- No secrets management integration with AWS Secrets Manager
- No service mesh or advanced networking

**3. Missing CI/CD Pipeline**
- No container registry (ECR) setup
- No automated build and deployment pipeline
- No GitOps workflow

**4. Incomplete Observability**
- No logging aggregation (CloudWatch Logs)
- No metrics collection (Prometheus/CloudWatch)
- No distributed tracing
- No alerting system

**5. Security Hardening Needed**
- No network policies
- No pod security policies/standards
- No IAM roles for service accounts (IRSA)
- No certificate management

**6. Scalability Enhancements**
- No cluster autoscaler
- No advanced HPA with custom metrics
- No database read replicas configuration

---

## Proposed Architecture

### High-Level AWS + Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        VPC: 10.0.0.0/16                              │  │
│  │  ┌────────────────┐  ┌──────────────────────────────────────────┐  │  │
│  │  │ Public Subnets │  │         Private Subnets                  │  │  │
│  │  │                │  │  ┌────────────────────────────────────┐  │  │  │
│  │  │ - ALB          │→ │  │      EKS Cluster                   │  │  │  │
│  │  │ - NAT Gateway  │  │  │  ┌──────────────────────────────┐ │  │  │  │
│  │  │ - Route 53     │  │  │  │   Worker Nodes (Auto Scaling)│ │  │  │  │
│  │  └────────────────┘  │  │  │  - API Gateway Pods x3      │ │  │  │  │
│  │                      │  │  │  - EDC Service Pods x2-10   │ │  │  │  │
│  │                      │  │  │  - Data Gen Service x1-5    │ │  │  │  │
│  │                      │  │  │  - Analytics Service x2-8   │ │  │  │  │
│  │                      │  │  │  - Quality Service x2-6     │ │  │  │  │
│  │                      │  │  │  - Security Service x2-5    │ │  │  │  │
│  │                      │  │  │  - Daft Analytics x1-3      │ │  │  │  │
│  │                      │  │  └──────────────────────────────┘ │  │  │  │
│  │                      │  └────────────────────────────────────┘  │  │  │
│  │                      │  ┌────────────────────────────────────┐  │  │  │
│  │                      │  │   Database Subnet                  │  │  │  │
│  │                      │  │  - RDS PostgreSQL (Multi-AZ)       │  │  │  │
│  │                      │  │  - ElastiCache Redis (Cluster)     │  │  │  │
│  │                      │  └────────────────────────────────────┘  │  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     Supporting Services                              │  │
│  │  - S3 Buckets (Documents, Generated Data, Backups)                  │  │
│  │  - ECR Container Registry                                           │  │
│  │  - Secrets Manager (DB Credentials, API Keys, Certificates)         │  │
│  │  - CloudWatch (Logs, Metrics, Alarms)                               │  │
│  │  - IAM Roles (IRSA for Pods, Service Accounts)                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: AWS EKS Infrastructure Setup (Week 1)

#### 1.1 EKS Cluster with Terraform

**New File:** `terraform/modules/eks/main.tf`

Create a comprehensive EKS module with:
- EKS cluster (v1.28+)
- Managed node groups (3 types: general, compute-intensive, memory-optimized)
- Cluster autoscaler
- VPC CNI plugin configuration
- CoreDNS configuration
- OIDC provider for IRSA

**New Files:**
- `terraform/modules/eks/variables.tf`
- `terraform/modules/eks/outputs.tf`

#### 1.2 ECR Container Registry

**Update:** `terraform/main.tf`

Add ECR repositories for each microservice:
- `clinical-trials/api-gateway`
- `clinical-trials/edc-service`
- `clinical-trials/data-generation-service`
- `clinical-trials/analytics-service`
- `clinical-trials/quality-service`
- `clinical-trials/security-service`
- `clinical-trials/daft-analytics-service`

#### 1.3 Enhanced RDS Configuration

**Update:** `terraform/main.tf`

Enhancements:
- Add read replicas for analytics workloads
- Enable automated backups to S3
- Configure parameter groups for performance
- Add CloudWatch alarms for database metrics

#### 1.4 Application Load Balancer

**New File:** `terraform/modules/alb/main.tf`

Configure ALB with:
- HTTPS listeners (port 443)
- SSL/TLS certificates from ACM
- Target groups for EKS Ingress
- Health checks
- Access logs to S3

---

### Phase 2: Enhanced Kubernetes Manifests (Week 1-2)

#### 2.1 Ingress Controller

**New File:** `kubernetes/ingress/nginx-ingress-controller.yaml`

Deploy NGINX Ingress Controller with:
- AWS NLB integration
- SSL termination
- Rate limiting
- Request routing rules

**New File:** `kubernetes/ingress/clinical-trials-ingress.yaml`

Configure ingress rules for:
- `/api/*` → API Gateway service
- `/docs` → API documentation
- `/health` → Health check endpoints

#### 2.2 Persistent Volume Claims

**New File:** `kubernetes/storage/storage-class.yaml`

Define storage classes:
- `gp3-encrypted` - General purpose SSD
- `io2-high-perf` - High-performance for databases

**New Files:**
- `kubernetes/storage/pvc-postgres.yaml`
- `kubernetes/storage/pvc-redis.yaml`

#### 2.3 ConfigMaps and Secrets

**Update:** `kubernetes/configmaps/`

Create ConfigMaps for:
- Application configuration
- Environment-specific settings
- Feature flags

**New File:** `kubernetes/secrets/external-secrets.yaml`

Integrate AWS Secrets Manager using External Secrets Operator:
- Database credentials
- JWT secrets
- API keys (OpenAI, etc.)
- Encryption keys

#### 2.4 Enhanced Service Definitions

**Update:** `kubernetes/services/all-services.yaml`

Add:
- Service annotations for AWS Load Balancer Controller
- Internal vs external service types
- Session affinity configuration

#### 2.5 Network Policies

**New Files:**
- `kubernetes/network-policies/default-deny.yaml`
- `kubernetes/network-policies/allow-api-gateway.yaml`
- `kubernetes/network-policies/allow-database.yaml`

Implement zero-trust networking:
- Default deny all traffic
- Explicit allow rules for service-to-service communication
- Database access restricted to specific services

#### 2.6 Pod Security Standards

**New File:** `kubernetes/security/pod-security-standards.yaml`

Apply pod security standards:
- Restricted mode for production workloads
- Non-root containers
- Read-only root filesystems
- Drop all capabilities

---

### Phase 3: Observability & Monitoring (Week 2)

#### 3.1 Prometheus & Grafana

**New Directory:** `kubernetes/monitoring/`

Deploy monitoring stack:
- Prometheus Operator
- Grafana with pre-configured dashboards
- Service monitors for all microservices
- Alert rules for critical metrics

**New Files:**
- `kubernetes/monitoring/prometheus-values.yaml`
- `kubernetes/monitoring/grafana-dashboards.yaml`

#### 3.2 CloudWatch Integration

**New File:** `kubernetes/monitoring/cloudwatch-agent.yaml`

Deploy CloudWatch Container Insights:
- Cluster-level metrics
- Pod-level metrics
- Application logs aggregation

**New File:** `kubernetes/monitoring/fluentd-cloudwatch.yaml`

Configure Fluentd for log shipping to CloudWatch Logs.

#### 3.3 Distributed Tracing

**New File:** `kubernetes/monitoring/jaeger.yaml`

Deploy Jaeger for distributed tracing:
- Trace collection from all services
- Service dependency visualization
- Performance bottleneck identification

---

### Phase 4: CI/CD Pipeline (Week 2-3)

#### 4.1 GitHub Actions Workflows

**New File:** `.github/workflows/build-and-push.yml`

Automated pipeline:
- Build Docker images for all services
- Run security scans (Trivy)
- Push to ECR
- Tag with git commit SHA and semantic version

**New File:** `.github/workflows/deploy-to-eks.yml`

Deployment pipeline:
- Update Kubernetes manifests with new image tags
- Apply manifests to EKS cluster
- Wait for rollout completion
- Run smoke tests
- Rollback on failure

#### 4.2 Helm Charts (Optional but Recommended)

**New Directory:** `helm/clinical-trials/`

Convert Kubernetes manifests to Helm charts for:
- Easier version management
- Environment-specific values
- Templating and reusability

---

### Phase 5: Advanced Features (Week 3-4)

#### 5.1 Cluster Autoscaler

**New File:** `kubernetes/autoscaling/cluster-autoscaler.yaml`

Configure cluster autoscaler to:
- Scale node groups based on pending pods
- Respect pod disruption budgets
- Optimize for cost and performance

#### 5.2 Vertical Pod Autoscaler (VPA)

**New File:** `kubernetes/autoscaling/vpa-recommendations.yaml`

Deploy VPA to:
- Analyze resource usage patterns
- Recommend optimal resource requests/limits
- Auto-update pod resources (optional)

#### 5.3 Service Mesh (Istio - Optional)

**New Directory:** `kubernetes/service-mesh/`

Deploy Istio for:
- Mutual TLS between services
- Advanced traffic management (canary deployments)
- Circuit breaking and retries
- Observability enhancements

#### 5.4 Backup and Disaster Recovery

**New File:** `kubernetes/backup/velero.yaml`

Deploy Velero for:
- Automated cluster backups to S3
- Disaster recovery procedures
- Migration capabilities

---

### Phase 6: Cost Optimization (Ongoing)

#### 6.1 Spot Instances for Non-Critical Workloads

**Update:** `terraform/modules/eks/main.tf`

Add spot instance node groups for:
- Data generation workers (fault-tolerant)
- Analytics batch jobs
- Development/staging environments

#### 6.2 Resource Right-Sizing

**New File:** `scripts/analyze-resource-usage.sh`

Script to:
- Analyze actual resource usage
- Compare with requests/limits
- Generate recommendations for optimization

#### 6.3 Auto-Shutdown for Non-Production

**New File:** `kubernetes/cronjobs/auto-shutdown.yaml`

CronJob to:
- Scale down dev/staging environments after hours
- Scale up before business hours
- Reduce costs by 60-70% for non-production

---

## Deployment Strategy

### Environment Strategy

| Environment | Purpose | Infrastructure | Cost |
|------------|---------|----------------|------|
| Development | Local testing | Minikube/Docker Compose | $0 |
| Staging | Pre-production testing | EKS (t3.medium x2, single-AZ) | ~$150/month |
| Production | Live workloads | EKS (t3.large x3-10, multi-AZ) | ~$500-1500/month |

### Deployment Workflow

```
Code Commit
     ↓
GitHub Actions
     ↓
Tests Pass? ──No──> Notify Developer
     ↓ Yes
Build Docker Images
     ↓
Push to ECR
     ↓
Update K8s Manifests
     ↓
Deploy to Staging
     ↓
Staging Tests Pass? ──No──> Notify Developer
     ↓ Yes
Manual Approval
     ↓
Deploy to Production
     ↓
Health Checks
     ↓
Healthy? ──No──> Auto Rollback
     ↓ Yes
Deployment Complete
```

---

## Security Considerations

### 1. Network Security
- ✅ VPC with private subnets for EKS and databases
- ✅ Security groups with least-privilege access
- ✅ Network policies for pod-to-pod communication
- ✅ WAF rules on ALB (optional)

### 2. Identity and Access Management
- ✅ IAM roles for service accounts (IRSA)
- ✅ Separate IAM roles per microservice
- ✅ AWS Secrets Manager for sensitive data
- ✅ Encryption at rest and in transit

### 3. Compliance (HIPAA)
- ✅ Encrypted RDS with automated backups
- ✅ Audit logging to CloudWatch
- ✅ PHI encryption in application layer
- ✅ Access controls and authentication

### 4. Container Security
- ✅ Non-root containers
- ✅ Image scanning with Trivy
- ✅ Minimal base images (Alpine/Distroless)
- ✅ Regular security updates

---

## Cost Estimation

### Monthly AWS Costs (Production)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| EKS Control Plane | 1 cluster | $73 |
| EC2 Instances (EKS Nodes) | 3x t3.large (on-demand) | ~$190 |
| EC2 Instances (EKS Nodes) | 2x t3.large (spot, 70% discount) | ~$40 |
| RDS PostgreSQL | db.t3.medium, Multi-AZ | ~$120 |
| ElastiCache Redis | cache.t3.medium x2 | ~$100 |
| Application Load Balancer | 1 ALB | ~$25 |
| NAT Gateway | 1 NAT Gateway | ~$35 |
| S3 Storage | 100 GB | ~$3 |
| ECR Storage | 50 GB | ~$5 |
| CloudWatch Logs | 10 GB/month | ~$5 |
| Data Transfer | 100 GB/month | ~$9 |
| Secrets Manager | 10 secrets | ~$4 |
| **Total** | | **~$609/month** |

### Cost Optimization Strategies

- **Use Spot Instances**: Save 60-70% on compute for fault-tolerant workloads
- **Reserved Instances**: Save 30-40% for predictable workloads (1-year commitment)
- **Auto-Scaling**: Scale down during off-hours
- **S3 Lifecycle Policies**: Move old data to Glacier
- **Right-Sizing**: Use VPA recommendations to optimize resource requests

**Optimized Production Cost:** ~$400-450/month

---

## Migration Path

### Step-by-Step Migration from Local to AWS

#### Week 1: Infrastructure Setup
- ✅ Run Terraform to create AWS infrastructure
- ✅ Create EKS cluster
- ✅ Set up ECR and push initial images
- ✅ Configure kubectl to access EKS cluster

#### Week 2: Deploy to Staging
- ✅ Deploy all microservices to staging EKS
- ✅ Configure Ingress and test external access
- ✅ Migrate database schema to RDS
- ✅ Run integration tests

#### Week 3: Monitoring & CI/CD
- ✅ Set up Prometheus and Grafana
- ✅ Configure CloudWatch integration
- ✅ Implement GitHub Actions pipelines
- ✅ Test automated deployments

#### Week 4: Production Deployment
- ✅ Deploy to production EKS
- ✅ Configure DNS and SSL certificates
- ✅ Run load tests
- ✅ Enable monitoring and alerting
- ✅ Document runbooks

---

## Success Metrics

### Performance Targets
- ✅ API response time: p95 < 500ms
- ✅ Data generation throughput: >100K records/second
- ✅ System uptime: 99.9% (SLA)
- ✅ Auto-scaling response time: < 2 minutes

### Scalability Targets
- ✅ Support 1M+ synthetic records generation
- ✅ Handle 1000+ concurrent users
- ✅ Scale from 3 to 20 nodes automatically
- ✅ Database supports 10K+ connections

### Cost Targets
- ✅ Production environment: < $500/month
- ✅ Staging environment: < $150/month
- ✅ Cost per 1M records generated: < $0.50

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| EKS cluster failure | High | Multi-AZ deployment, automated backups |
| Database corruption | High | Automated backups, point-in-time recovery |
| Cost overrun | Medium | Budget alerts, auto-shutdown for non-prod |
| Security breach | High | Network policies, IRSA, encryption, audit logs |
| Deployment failure | Medium | Blue-green deployments, automated rollback |
| Vendor lock-in | Low | Use Kubernetes (portable), avoid AWS-specific features |

---

## Next Steps

### Immediate Actions (This Week)
1. Review and approve this plan
2. Set up AWS account and configure billing alerts
3. Create GitHub repository for infrastructure code
4. Assign team members to each phase

### Questions for Stakeholders
1. **Budget**: What is the approved monthly budget for AWS infrastructure?
2. **Timeline**: Is the 4-week timeline acceptable, or do we need to accelerate?
3. **Environments**: Do we need separate AWS accounts for staging and production?
4. **Compliance**: Are there specific HIPAA compliance requirements we must address?
5. **Domain**: Do we have a domain name for the production deployment?
6. **Monitoring**: Do we have existing monitoring tools (Datadog, New Relic) to integrate with?

---

## Appendix

### A. Useful Commands

```bash
# Terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# EKS
aws eks update-kubeconfig --name clinical-trials-cluster --region us-east-1

# Kubernetes
kubectl get pods -n clinical-trials
kubectl logs -f deployment/api-gateway -n clinical-trials
kubectl describe hpa -n clinical-trials

# ECR Login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### B. Reference Documentation
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [HIPAA on AWS](https://aws.amazon.com/compliance/hipaa-compliance/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### C. Team Training Resources
- [EKS Workshop](https://www.eksworkshop.com/)
- [Kubernetes Fundamentals](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [AWS Solutions Architect Associate](https://aws.amazon.com/certification/certified-solutions-architect-associate/)

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-21  
**Author:** AI Assistant  
**Status:** Ready for Review