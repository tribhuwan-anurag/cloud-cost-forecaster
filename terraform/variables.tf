variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for naming resources"
  type        = string
  default     = "cloud-cost-forecaster"
}

variable "alert_email" {
  description = "Email address for cost alert notifications"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}