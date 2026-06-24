#!/usr/bin/env bash
# Install commit-reviewer globally under ~/.local (no shell venv activation).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/commit-reviewer"
VENV="$INSTALL_ROOT/venv"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/commit-reviewer"
WEB_DST="$ROOT/backend/commit_reviewer/web"

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

need_cmd python3
need_cmd npm

PYTHON_VERSION="$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || die "Python 3.10+ is required (found $PYTHON_VERSION)"

info "Building frontend"
(
  cd "$ROOT/frontend"
  if [[ -f package-lock.json ]]; then
    npm ci
  else
    npm install
  fi
  npm run build
)

info "Bundling web assets into the Python package"
rm -rf "$WEB_DST"
cp -a "$ROOT/frontend/dist" "$WEB_DST"

info "Creating isolated environment at $VENV"
mkdir -p "$INSTALL_ROOT"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip wheel
"$VENV/bin/pip" install "$ROOT/backend"

info "Installing command-line wrappers"
mkdir -p "$BIN_DIR"
cat >"$BIN_DIR/review-commits" <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/review-commits" "\$@"
EOF
chmod +x "$BIN_DIR/review-commits"
ln -sf review-commits "$BIN_DIR/commit-reviewer"

mkdir -p "$CONFIG_DIR"
configure_api_key

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  warn "$BIN_DIR is not on your PATH."
  warn "Add this to your shell profile: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

info "Installed successfully."
printf '\nRun from any git repository:\n  review-commits\n\n'
printf 'Uninstall later:\n  %s/uninstall.sh\n' "$ROOT"
