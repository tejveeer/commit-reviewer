#!/usr/bin/env bash
# Install commit-reviewer via Docker (wrapper under ~/.local/bin).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/commit-reviewer"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/commit-reviewer"
IMAGE="commit-reviewer:latest"

info() { printf '==> %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

read_env_value() {
  local file="$1" key="$2"
  [[ -f "$file" ]] || return 0
  local line
  line="$(grep -E "^${key}=" "$file" 2>/dev/null | head -1 || true)"
  [[ -n "$line" ]] || return 0
  printf '%s' "${line#*=}"
}

configure_api_key() {
  local existing_key="" repo_key="" api_key=""

  existing_key="$(read_env_value "$CONFIG_DIR/.env" OPENROUTER_API_KEY)"
  repo_key="$(read_env_value "$ROOT/.env" OPENROUTER_API_KEY)"

  if [[ -n "$existing_key" ]]; then
    read -rsp "OpenRouter API key already configured. Press Enter to keep it, or enter a new key: " api_key
    printf '\n'
    if [[ -z "$api_key" ]]; then
      api_key="$existing_key"
    fi
  elif [[ -n "$repo_key" ]]; then
    read -rsp "Enter your OpenRouter API key [leave blank to use key from $ROOT/.env]: " api_key
    printf '\n'
    if [[ -z "$api_key" ]]; then
      api_key="$repo_key"
    fi
  else
    while [[ -z "$api_key" ]]; do
      read -rsp "Enter your OpenRouter API key: " api_key
      printf '\n'
      if [[ -z "$api_key" ]]; then
        warn "An API key is required. Create one at https://openrouter.ai/keys"
      fi
    done
  fi

  {
    echo "# OpenRouter API key for commit-reviewer."
    echo "# Create a free key at https://openrouter.ai/keys"
    printf 'OPENROUTER_API_KEY=%s\n' "$api_key"
  } >"$CONFIG_DIR/.env"
  info "Saved API key to $CONFIG_DIR/.env"
}

need_cmd docker
if ! docker info >/dev/null 2>&1; then
  die "Docker is installed but the daemon is not running. Start Docker and try again."
fi

info "Building Docker image ($IMAGE)"
docker build -t "$IMAGE" "$ROOT"

info "Installing command-line wrappers"
mkdir -p "$INSTALL_ROOT" "$BIN_DIR" "$CONFIG_DIR"
printf '%s\n' "$IMAGE" >"$INSTALL_ROOT/image"

cat >"$BIN_DIR/review-commits" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/commit-reviewer"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/commit-reviewer"
ENV_FILE="$CONFIG_DIR/.env"
IMAGE_FILE="$INSTALL_ROOT/image"
IMAGE="commit-reviewer:latest"

if [[ -f "$IMAGE_FILE" ]]; then
  IMAGE="$(tr -d '[:space:]' <"$IMAGE_FILE")"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  printf 'error: Missing %s — run install.sh first.\n' "$ENV_FILE" >&2
  exit 1
fi

PORT=3546
NO_SERVE=0
args=("$@")
i=0
while (( i < ${#args[@]} )); do
  arg="${args[$i]}"
  case "$arg" in
    --port)
      ((i++))
      PORT="${args[$i]:-3546}"
      ;;
    --port=*)
      PORT="${arg#*=}"
      ;;
    --no-serve)
      NO_SERVE=1
      ;;
  esac
  ((i++))
done

docker_args=(
  run --rm -it
  --env-file "$ENV_FILE"
  -e COMMIT_REVIEWER_HOST=0.0.0.0
  -v "$(pwd):$(pwd)"
  -w "$(pwd)"
)

if [[ "$NO_SERVE" -eq 0 ]]; then
  docker_args+=(-p "${PORT}:${PORT}")
fi

exec docker "${docker_args[@]}" "$IMAGE" "$@"
EOF
chmod +x "$BIN_DIR/review-commits"
ln -sf review-commits "$BIN_DIR/commit-reviewer"

configure_api_key

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  warn "$BIN_DIR is not on your PATH."
  warn "Add this to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

info "Installed successfully."
printf '\nRun from any git repository:\n  review-commits\n\n'
printf 'Uninstall later:\n  %s/uninstall.sh\n' "$ROOT"
