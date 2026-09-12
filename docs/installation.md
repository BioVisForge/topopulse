# Installation

Python 3.11+ is required. Wheels bundle the Rust extension. MP4 and WebM output require FFmpeg.

```bash
pip install topopulse
```

For contributors:

```bash
git clone https://github.com/BioVisForge/topopulse.git
cd topopulse
uv sync --all-extras
uv run maturin develop
```

Check `ffmpeg -version` before requesting MP4 output.

