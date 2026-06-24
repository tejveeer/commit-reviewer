#!/usr/bin/env bash
# Remove the global commit-reviewer installation.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/commit-reviewer"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/commit-reviewer"
IMAGE="commit-reviewer:latest"

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

PURGE=0
REMOVE_IMAGE=0
for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=1 ;;
    --remove-image) REMOVE_IMAGE=1 ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") [--purge] [--remove-image]

  --purge         Also remove $CONFIG_DIR (API key and settings)
  --remove-image  Also remove the Docker image ($IMAGE)
EOF
      exit 0
      ;;
    *)
      warn "Unknown option: $arg (use --help)"
      exit 1
      ;;
  esac
done

removed=0

if [[ -d "$INSTALL_ROOT" ]]; then
  info "Removing $INSTALL_ROOT"
  rm -rf "$INSTALL_ROOT"
  removed=1
fi

for cmd in review-commits commit-reviewer; do
  if [[ -e "$BIN_DIR/$cmd" ]]; then
    info "Removing $BIN_DIR/$cmd"
    rm -f "$BIN_DIR/$cmd"
    removed=1
  fi
done

if [[ "$REMOVE_IMAGE" -eq 1 ]]; then
  if command -v docker >/dev/null 2>&1 && docker image inspect "$IMAGE" >/dev/null 2>&1; then
    info "Removing Docker image $IMAGE"
    docker rmi "$IMAGE"
    removed=1
  else
    warn "Docker image $IMAGE not found — skipping"
  fi
fi

if [[ "$PURGE" -eq 1 && -d "$CONFIG_DIR" ]]; then
  info "Removing $CONFIG_DIR"
  rm -rf "$CONFIG_DIR"
elif [[ -d "$CONFIG_DIR" ]]; then
  info "Kept config at $CONFIG_DIR (use --purge to remove)"
fi

if [[ "$removed" -eq 0 ]]; then
  warn "Nothing to uninstall — commit-reviewer does not appear to be installed."
  exit 0
fi

info "Uninstalled successfully."
