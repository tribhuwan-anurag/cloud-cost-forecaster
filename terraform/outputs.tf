output "s3_bucket_name" {
  description = "S3 bucket for reports"
  value       = aws_s3_bucket.reports.bucket
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "iam_role_arn" {
  description = "IAM role ARN for the forecaster"
  value       = aws_iam_role.forecaster.arn
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}