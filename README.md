# Commit Reviewer

Commit Reviewer reads recent git commit messages, sends them to an LLM for feedback, and opens an interactive report in your browser. Each commit gets a rating and short explanation so you can spot weak messages and improve how you write commits over time.

## Prerequisites

- Python 3.10+
- Node.js and npm (needed only for installation)
- Git
- An [OpenRouter](https://openrouter.ai/keys) API key

## Install

Clone the repository and run the install script:

```bash
git clone https://github.com/tejveeer/commit-reviewer.git
cd commit-reviewer
./install.sh
```

The script builds the web UI, installs the app under `~/.local`, and prompts for your OpenRouter API key.

To remove the install:

```bash
./uninstall.sh
```

Make sure `~/.local/bin` is on your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

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
