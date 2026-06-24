# Commit Reviewer

Commit Reviewer reads recent git commit messages, sends them to an LLM for feedback, and opens an interactive report in your browser. Each commit gets a rating and short explanation so you can spot weak messages and improve how you write commits over time.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (Docker Desktop on macOS/Windows, or Docker Engine on Linux)
- Git (on the host, for local repositories)
- An [OpenRouter](https://openrouter.ai/keys) API key

Node.js and Python are **not** required on the host — the install script builds everything inside a Docker image.

## Install

Clone the repository and run the install script:

```bash
git clone https://github.com/tejveeer/commit-reviewer.git
cd commit-reviewer
./install.sh
```

The script builds a Docker image, installs a `review-commits` wrapper under `~/.local/bin`, and prompts for your OpenRouter API key.

Make sure Docker is running before you install. On Linux, your user may need to be in the `docker` group.

Make sure `~/.local/bin` is on your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

To remove the install:

```bash
./uninstall.sh
```

Pass `--remove-image` to also delete the Docker image, and `--purge` to remove your saved API key.

## Usage

Run `review-commits` from a local repository:

```bash
cd /path/to/your/repo
review-commits
```

Or review a remote repository without cloning it locally:

```bash
review-commits --url https://github.com/user/repo.git
```

The tool reviews recent commits, prints progress in the terminal, and serves a report at `http://localhost:3546/`. Press `Ctrl+C` to stop the server when you are done.

Your API key is stored in `~/.config/commit-reviewer/.env`.

### WSL

Run the install from an **Ubuntu terminal** with Docker installed inside WSL (Docker Desktop with WSL integration, or Docker Engine in WSL). You do not need Node.js in WSL anymore.

## Development

To rebuild after pulling changes:

```bash
./install.sh
```

Or build and run the image directly:

```bash
docker build -t commit-reviewer:latest .
docker run --rm -it \
  --env-file ~/.config/commit-reviewer/.env \
  -e COMMIT_REVIEWER_HOST=0.0.0.0 \
  -p 3546:3546 \
  -v "$(pwd):$(pwd)" \
  -w "$(pwd)" \
  commit-reviewer:latest
```

For local development without Docker, see the backend and frontend directories and use a Python virtualenv plus `npm run build` in `frontend/`.
