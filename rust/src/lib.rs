mod errors;
mod filter;
mod graph;
mod indexing;
mod normalize;
mod python;
mod stats;
mod streaming;
mod temporal;

use pyo3::prelude::*;

#[pymodule]
fn _rust(module: &Bound<'_, PyModule>) -> PyResult<()> {
    python::register(module)
}
