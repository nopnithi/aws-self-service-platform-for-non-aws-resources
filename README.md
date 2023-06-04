# Self-Service Platform on AWS for Managing Non-AWS Resources

This project is designed to provide users a self-service platform on AWS, enabling them to manage resources outside AWS. The main technologies used are

- AWS Service Catalog
- AWS IAM
- AWS CloudFormation
- AWS Lambda (with Python)
- AWS Secrets Manager
- Azure DevOps for Git repository and pipeline
- Terraform
- Bash

## How It Works

Users interact with the AWS Service Catalog, where they input data following our defined UI. The AWS IAM ensures proper authorization. AWS CloudFormation captures these inputs and passes them to an AWS Lambda function, which uses Python code to clone Terraform files, generates .tfvars files, and pushes them back to a remote Git repository.

The Terraform files, stored in Azure DevOps, are used to create resources outside AWS, guided by the .tfvars files. If a .tfvars file is pushed, an automation pipeline creates a Terraform workspace and runs Terraform to create resources as per the file.

## Code Used in This Project

This repository contains all code used in this project, except for the Terraform code, which pertains to my personal information. The main code includes:

- CloudFormation Template: Used to create the user interface in AWS Service Catalog.
- Lambda Python Code: Uses the `crhelper` for easier code writing for CloudFormation Custom Resource, and `GitPython` and `pytz` libraries.
- Azure Pipeline YAML: Defines the logic on the pipeline.

For a more detailed description, please check [the full article](https://nopnithi.medium.com/สร้าง-self-service-platform-บน-aws-ให้-user-จัดการ-non-aws-resource-เอง-46f591cc038) on my Medium blog.
