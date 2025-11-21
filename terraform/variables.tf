# variables.tf - Terraform variables for AWS infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"  # Free tier eligible
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"  # Free tier eligible
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "clinical-trials"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "ClinicalTrials"
    ManagedBy   = "Terraform"
    Repository  = "synthetictrial-enterprise"
  }
}

# ========== EKS VARIABLES ==========

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS nodes"
  type        = string
  default     = "t3.medium"  # 2 vCPU, 4GB RAM - good for staging
}

variable "eks_desired_nodes" {
  description = "Desired number of EKS worker nodes"
  type        = number
  default     = 2  # Start small for staging
}

variable "eks_min_nodes" {
  description = "Minimum number of EKS worker nodes"
  type        = number
  default     = 1
}

variable "eks_max_nodes" {
  description = "Maximum number of EKS worker nodes"
  type        = number
  default     = 5  # Allow scaling up for load testing
}
