#!/usr/bin/env bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO_ROOT

export PROJECT_ACCOUNT="${PROJECT_ACCOUNT:-project_462000131}"
export LUMI_USER="${LUMI_USER:-${USER:-anisrahm}}"
export CONTAINER="${CONTAINER:-/appl/local/laifs/containers/lumi-multitorch-u24r64f21m43t29-20260225_144743/lumi-multitorch-full-u24r64f21m43t29-20260225_144743.sif}"

export AITTA_REPO_NAME="${AITTA_REPO_NAME:-$(basename "${REPO_ROOT}")}"
export AITTA_DATA_ROOT="${AITTA_DATA_ROOT:-/scratch/${PROJECT_ACCOUNT}/${LUMI_USER}/${AITTA_REPO_NAME}/data}"
export AITTA_OUTPUT_ROOT="${AITTA_OUTPUT_ROOT:-/scratch/${PROJECT_ACCOUNT}/${LUMI_USER}/${AITTA_REPO_NAME}/outputs}"
export AITTA_REPORT_ROOT="${AITTA_REPORT_ROOT:-/project/${PROJECT_ACCOUNT}/${LUMI_USER}/${AITTA_REPO_NAME}/reports}"
export AITTA_VENV="${AITTA_VENV:-/scratch/${PROJECT_ACCOUNT}/${LUMI_USER}/${AITTA_REPO_NAME}/.venv}"
