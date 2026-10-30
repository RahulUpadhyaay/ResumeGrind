#!/bin/bash
# =============================================================================
# ResumeGrind Deployment Script
# =============================================================================
# WHY a deploy script?
# Instead of remembering 10 different commands, you run ONE script.
# This is how production teams automate deployments (CI/CD pipelines
# execute scripts like this). It shows recruiters you understand DevOps.
# =============================================================================

set -e  # WHY: Exit immediately if any command fails. Prevents partial deployments.

# Colors for terminal output (makes deployment logs readable)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}  # WHY: Default to 'dev' if no argument provided
STACK_NAME="resumegrind-${ENVIRONMENT}"
REGION=${AWS_REGION:-ap-south-1}  # WHY: Default to Mumbai region (closest to India)
FRONTEND_DIR="../frontend"
BACKEND_DIR="../backend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ResumeGrind Deployment (${ENVIRONMENT})${NC}"
echo -e "${BLUE}========================================${NC}"

# ─── Step 1: Validate Prerequisites ────────────────────────────────────────
echo -e "\n${YELLOW}[1/6] Checking prerequisites...${NC}"

if ! command -v sam &> /dev/null; then
    echo -e "${RED}ERROR: AWS SAM CLI not found. Install it from:${NC}"
    echo "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found. Install it from:${NC}"
    echo "https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js not found. Install it from: https://nodejs.org${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites found${NC}"

# ─── Step 2: Build Backend ──────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/6] Building backend...${NC}"

cd "${BACKEND_DIR}"
pip install -r requirements.txt -t ./package/ --quiet
# WHY install to ./package? SAM packages the Lambda code as a ZIP.
# All dependencies must be in the same directory as our code.
cp -r app/ ./package/
cp lambda_handler.py ./package/
cd ..

echo -e "${GREEN}✓ Backend built successfully${NC}"

# ─── Step 3: Build Frontend ─────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/6] Building frontend...${NC}"

cd "${FRONTEND_DIR}"
npm install --silent
npm run build
# WHY npm run build? Vite compiles React JSX, tree-shakes unused code,
# minifies JavaScript, and outputs optimized static files to dist/
cd ..

echo -e "${GREEN}✓ Frontend built successfully${NC}"

# ─── Step 4: Deploy AWS Infrastructure ──────────────────────────────────────
echo -e "\n${YELLOW}[4/6] Deploying AWS infrastructure with SAM...${NC}"

cd infrastructure

sam build --template-file template.yaml
# WHY sam build? It resolves dependencies, packages Lambda code,
# and prepares artifacts for deployment.

sam deploy \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --parameter-overrides \
        Environment="${ENVIRONMENT}" \
        GeminiApiKey="${GEMINI_API_KEY}" \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset
# WHY these flags?
# --capabilities CAPABILITY_IAM: Required when template creates IAM roles
# --resolve-s3: Auto-creates an S3 bucket for deployment artifacts
# --no-confirm-changeset: Auto-approve changes (remove for production)
# --no-fail-on-empty-changeset: Don't error if nothing changed

cd ..

echo -e "${GREEN}✓ AWS infrastructure deployed${NC}"

# ─── Step 5: Upload Frontend to S3 ──────────────────────────────────────────
echo -e "\n${YELLOW}[5/6] Uploading frontend to S3...${NC}"

# Get the frontend bucket name from CloudFormation outputs
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text 2>/dev/null || echo "")

if [ -z "${FRONTEND_BUCKET}" ] || [ "${FRONTEND_BUCKET}" = "None" ]; then
    # Fallback: construct bucket name manually
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    FRONTEND_BUCKET="resumegrind-frontend-${ENVIRONMENT}-${ACCOUNT_ID}"
fi

aws s3 sync "${FRONTEND_DIR}/dist/" "s3://${FRONTEND_BUCKET}/" \
    --delete \
    --region "${REGION}"
# WHY --delete? Removes files from S3 that no longer exist in dist/.
# This ensures the deployed version exactly matches the build output.

echo -e "${GREEN}✓ Frontend uploaded to S3${NC}"

# ─── Step 6: Print Deployment Summary ───────────────────────────────────────
echo -e "\n${YELLOW}[6/6] Fetching deployment info...${NC}"

API_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
    --output text)

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  ✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "  🌐 Frontend URL:  ${BLUE}${FRONTEND_URL}${NC}"
echo -e "  🔌 API URL:       ${BLUE}${API_URL}${NC}"
echo -e "  📦 S3 Bucket:     ${BLUE}${FRONTEND_BUCKET}${NC}"
echo -e "  🌍 Region:        ${BLUE}${REGION}${NC}"
echo -e "  🏷️  Environment:   ${BLUE}${ENVIRONMENT}${NC}"
echo -e ""
echo -e "${YELLOW}To tear down: aws cloudformation delete-stack --stack-name ${STACK_NAME}${NC}"
