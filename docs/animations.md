# Animations

GIF, MP4, and WebM are implemented. Frames are rendered and encoded incrementally rather than
stored as a complete image stack.

`uniform` timing assigns one visual frame per sample. `proportional` repeats frames according to
numeric or datetime gaps. `custom` accepts one duration per sample. Irregular timestamps are never
silently treated as equally spaced when proportional timing is requested.

Metadata sidecars record the network hash, layout seed, mappings, normalization, filters, FPS,
resolution, codec, and time coordinate without private input paths.

