# Layouts

Supported layouts are spring, Kamada–Kawai, circular, shell, spectral, random, grid,
hierarchical (for DAGs), and fixed coordinates. Spring and random accept a reproducible seed.

```python
network.save_layout("layout.json")
network.load_layout("layout.json")
```

The default layout is computed once. Set `dynamic=True` only when movement itself is intentional;
stable positions are normally essential for comparing frames or conditions.

