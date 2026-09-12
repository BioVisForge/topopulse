# Troubleshooting

**Strict alignment failed:** inspect the reported missing and extra IDs. Change policy only when
that mismatch is scientifically intended.

**MP4 unavailable:** install FFmpeg and confirm `ffmpeg -version` is visible in the same shell.

**Nodes jump:** reuse the default static layout or save/load one JSON layout across experiments.

**Graph is unreadable:** reduce node/edge budgets and suppress labels; a 100,000-node graph should
be summarized, not drawn literally.

