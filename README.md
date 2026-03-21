# Cloud Cost Forecaster

A production-grade AWS cost intelligence pipeline that predicts month-end 
cloud spend and flags underutilized resources using time-series forecasting.

## What it does

- Pulls 90 days of billing data from AWS Cost Explorer API
- Trains a Prophet forecasting model to predict next 30 days of spend
- Classifies each AWS service as active, idle, or rising
- Detects cost anomalies (spikes above the 95% confidence interval)
- Generates a styled HTML report with forecast chart
- Runs automatically on a schedule via CI/CD

## Tech stack

| Layer | Tool |
|---|---|
| Language | Python 3.11 |
| Forecasting | Prophet (Meta) |
| Cloud | AWS (Cost Explorer, S3, ECR, IAM, SNS) |
| Infrastructure | Terraform |
| Containers | Docker |
| CI/CD | GitHub Actions |

## Project structure
```
cloud-cost-forecaster/
├── app/
│   ├── ingest.py       # AWS Cost Explorer data pull
│   ├── forecast.py     # Prophet time-series forecasting
│   ├── classify.py     # Service classification
│   ├── report.py       # HTML report generation
│   └── main.py         # Pipeline orchestrator
├── terraform/          # AWS infrastructure as code
├── .github/workflows/  # CI/CD pipelines
├── templates/          # Jinja2 HTML report template
└── tests/              # Pytest test suite
```

## Running locally
```bash
# Clone and set up
git clone https://github.com/YOUR_USERNAME/cloud-cost-forecaster
cd cloud-cost-forecaster
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure AWS credentials
cp .env.example .env
# Fill in your AWS credentials in .env

# Run the full pipeline
python3 app/main.py

# Open the report
open data/report.html
```

## Running with Docker
```bash
docker build -t cloud-cost-forecaster .
docker run --rm --env-file .env -v $(pwd)/data:/app/data cloud-cost-forecaster
```

## CI/CD Pipeline

Every push to `main` automatically:
1. Lints Python code with flake8
2. Runs 6 pytest unit tests
3. Builds Docker image
4. Pushes versioned image to AWS ECR

## Infrastructure (Terraform)
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Provisions: S3 bucket, ECR repository, IAM role, SNS alerts topic.
