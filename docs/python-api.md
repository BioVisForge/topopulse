# Python API

Primary object API: `DynamicNetwork.from_edgelist`, `.validate`, `.plot`, `.animate`, `.layout`,
`.save_layout`, and `.load_layout`.

Functional API: `plot_network`, `animate_network`, `animate_difference`, `animate_conditions`, and
`validate_network`. Operations return a path, Matplotlib figure, validation dictionary, or typed
`AnimationResult` as appropriate.

Configuration models are Pydantic types and reject unknown fields.

