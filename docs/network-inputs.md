# Network inputs

Implemented inputs are CSV/TSV edge lists, pandas DataFrames, NetworkX graphs, dictionaries/lists,
and GraphML. Required columns are `source,target`; supported types are `activation`, `inhibition`,
`undirected`, `reaction`, `transport`, `association`, and `unknown`.

Metadata columns such as weight, confidence, database, evidence, and reaction ID are preserved.
SBML, SBGN, CX/CX2, BioPAX, PEtab, and Neo4j/Cytoscape exports are adapter targets, not v0.1 claims.

