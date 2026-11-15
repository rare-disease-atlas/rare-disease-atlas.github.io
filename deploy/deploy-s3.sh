#!/usr/bin/env bash
# =============================================================================
# deploy-s3.sh — Production Static Deployment for rare-disease-atlas.github.io
#
# Uploads static HTML, CSS, Markdown (llms.txt / llms-full.txt / *.md), JSON
# (.well-known/*, opportunities.json), YAML (openapi.yaml), and XML/TXT files
# to AWS S3 with explicit agent-friendly MIME types & UTF-8 charsets, then
# optionally triggers a CloudFront cache invalidation.
#
# Usage:
#   S3_BUCKET=rare-disease-atlas.github.io \
#   CLOUDFRONT_DISTRIBUTION_ID=E1234567890ABC \
#   ./deploy/deploy-s3.sh [--dry-run]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SITE_DIR="${SITE_DIR:-${PROJECT_ROOT}/site}"

S3_BUCKET="${S3_BUCKET:-rare-disease-atlas.github.io}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CLOUDFRONT_DISTRIBUTION_ID="${CLOUDFRONT_DISTRIBUTION_ID:-}"

DRY_RUN_FLAG=()
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN_FLAG=("--dryrun")
  echo "[DRY-RUN] Simulating S3 upload to s3://${S3_BUCKET} (no remote changes will be made)"
fi

if [[ ! -d "${SITE_DIR}" ]]; then
  echo "Error: SITE_DIR does not exist at ${SITE_DIR}" >&2
  exit 1
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "Error: aws CLI not found in PATH. Install AWS CLI v2 first." >&2
  exit 1
fi

CACHE_DOC="public, max-age=300, s-maxage=3600, stale-while-revalidate=86400"
CACHE_STATIC="public, max-age=86400, s-maxage=604800"

echo "==> [1/7] Syncing HTML dossiers (text/html; charset=utf-8)..."
aws s3 sync "${SITE_DIR}/" "s3://${S3_BUCKET}/" \
  --region "${AWS_REGION}" \
  --exclude "*" \
  --include "*.html" \
  --content-type "text/html; charset=utf-8" \
  --cache-control "${CACHE_DOC}" \
  --metadata-directive REPLACE \
  "${DRY_RUN_FLAG[@]}"

echo "==> [2/7] Syncing Stylesheets (text/css; charset=utf-8)..."
aws s3 sync "${SITE_DIR}/" "s3://${S3_BUCKET}/" \
  --region "${AWS_REGION}" \
  --exclude "*" \
  --include "*.css" \
  --content-type "text/css; charset=utf-8" \
  --cache-control "${CACHE_STATIC}" \
  --metadata-directive REPLACE \
  "${DRY_RUN_FLAG[@]}"

echo "==> [3/7] Syncing Agent Markdown feeds & llms.txt (text/markdown; charset=utf-8)..."
aws s3 sync "${SITE_DIR}/" "s3://${S3_BUCKET}/" \
  --region "${AWS_REGION}" \
  --exclude "*" \
  --include "*.md" \
  --include "llms.txt" \
  --include "llms-full.txt" \
  --include "*/llms.txt" \
  --content-type "text/markdown; charset=utf-8" \
  --cache-control "${CACHE_DOC}" \
  --metadata-directive REPLACE \
  "${DRY_RUN_FLAG[@]}"

echo "==> [4/7] Syncing JSON datasets & .well-known manifests (application/json; charset=utf-8)..."
aws s3 sync "${SITE_DIR}/" "s3://${S3_BUCKET}/" \
  --region "${AWS_REGION}" \
  --exclude "*" \
  --include "*.json" \
  --content-type "application/json; charset=utf-8" \
  --cache-control "${CACHE_DOC}" \
  --metadata-directive REPLACE \
  "${DRY_RUN_FLAG[@]}"

echo "==> [5/7] Syncing OpenAPI / YAML specs (application/yaml; charset=utf-8)..."
aws s3 sync "${SITE_DIR}/" "s3://${S3_BUCKET}/" \
  --region "${AWS_REGION}" \
  --exclude "*" \
  --include "*.yaml" \
  --include "*.yml" \
  --content-type "application/yaml; charset=utf-8" \
  --cache-control "${CACHE_DOC}" \
  --metadata-directive REPLACE \
  "${DRY_RUN_FLAG[@]}"

echo "==> [6/7] Syncing XML Sitemap & robots.txt..."
if [[ -f "${SITE_DIR}/sitemap.xml" ]]; then
  aws s3 cp "${SITE_DIR}/sitemap.xml" "s3://${S3_BUCKET}/sitemap.xml" \
    --region "${AWS_REGION}" \
    --content-type "application/xml; charset=utf-8" \
    --cache-control "${CACHE_DOC}" \
    --metadata-directive REPLACE \
    "${DRY_RUN_FLAG[@]}"
fi

if [[ -f "${SITE_DIR}/robots.txt" ]]; then
  aws s3 cp "${SITE_DIR}/robots.txt" "s3://${S3_BUCKET}/robots.txt" \
    --region "${AWS_REGION}" \
    --content-type "text/plain; charset=utf-8" \
    --cache-control "${CACHE_DOC}" \
    --metadata-directive REPLACE \
    "${DRY_RUN_FLAG[@]}"
fi

echo "==> [7/7] Syncing any remaining static assets (SVG/PNG/ICO)..."
aws s3 sync "${SITE_DIR}/" "s3://${S3_BUCKET}/" \
  --region "${AWS_REGION}" \
  --exclude "*.html" \
  --exclude "*.css" \
  --exclude "*.md" \
  --exclude "llms.txt" \
  --exclude "llms-full.txt" \
  --exclude "*.json" \
  --exclude "*.yaml" \
  --exclude "*.yml" \
  --exclude "sitemap.xml" \
  --exclude "robots.txt" \
  --cache-control "${CACHE_STATIC}" \
  "${DRY_RUN_FLAG[@]}"

if [[ -n "${CLOUDFRONT_DISTRIBUTION_ID}" && ${#DRY_RUN_FLAG[@]} -eq 0 ]]; then
  echo "==> Creating CloudFront cache invalidation on ${CLOUDFRONT_DISTRIBUTION_ID}..."
  aws cloudfront create-invalidation \
    --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
    --paths "/*"
else
  echo "==> Skipping CloudFront invalidation (set CLOUDFRONT_DISTRIBUTION_ID to enable)."
fi

echo "==> Deployment complete for https://${S3_BUCKET}"
