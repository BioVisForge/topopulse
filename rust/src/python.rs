use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1, PyReadonlyArray2, PyUntypedArrayMethods};
use pyo3::prelude::*;

use crate::{
    errors::value_error, filter, graph::IndexedGraph, indexing, normalize, stats, streaming,
    temporal,
};

#[pyclass(name = "IndexedGraph")]
pub struct PyIndexedGraph {
    graph: IndexedGraph,
}

#[pymethods]
impl PyIndexedGraph {
    #[new]
    #[pyo3(signature = (sources, targets, edge_types=None, directed=true))]
    fn new(
        sources: Vec<String>,
        targets: Vec<String>,
        edge_types: Option<Vec<String>>,
        directed: bool,
    ) -> PyResult<Self> {
        let graph = IndexedGraph::build(
            &sources,
            &targets,
            edge_types.as_deref().unwrap_or(&[]),
            directed,
        )
        .map_err(value_error)?;
        Ok(Self { graph })
    }

    #[getter]
    fn node_ids(&self) -> Vec<String> {
        self.graph.node_ids.clone()
    }
    #[getter]
    fn sources<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<u32>> {
        self.graph.sources.clone().into_pyarray(py)
    }
    #[getter]
    fn targets<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<u32>> {
        self.graph.targets.clone().into_pyarray(py)
    }
    #[getter]
    fn edge_types(&self) -> Vec<String> {
        self.graph.edge_types.clone()
    }
    #[getter]
    fn directed(&self) -> bool {
        self.graph.directed
    }
    fn degrees<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<u32>> {
        self.graph.degrees().into_pyarray(py)
    }
    fn component_labels<'py>(&self, py: Python<'py>) -> Bound<'py, PyArray1<u32>> {
        self.graph.component_labels().into_pyarray(py)
    }
    fn duplicate_count(&self) -> usize {
        self.graph.duplicate_count()
    }
}

#[pyfunction]
fn alignment_index(
    graph_ids: Vec<String>,
    data_ids: Vec<String>,
    policy: &str,
) -> PyResult<(Vec<i64>, Vec<String>, Vec<String>)> {
    indexing::alignment_index(&graph_ids, &data_ids, policy).map_err(value_error)
}

#[pyfunction]
#[pyo3(signature = (values, mode, params=None))]
fn normalize_matrix<'py>(
    py: Python<'py>,
    values: PyReadonlyArray2<'py, f64>,
    mode: &str,
    params: Option<Vec<f64>>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let shape = values.shape();
    let rows = shape[0];
    let cols = shape[1];
    let slice = values
        .as_slice()
        .map_err(|_| value_error("values must be C-contiguous float64"))?;
    let result = py
        .allow_threads(|| {
            normalize::normalize(slice, rows, cols, mode, params.as_deref().unwrap_or(&[]))
        })
        .map_err(value_error)?;
    Ok(result.into_pyarray(py))
}

#[pyfunction]
fn interpolate_matrix<'py>(
    py: Python<'py>,
    values: PyReadonlyArray2<'py, f64>,
    factor: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let shape = values.shape();
    let slice = values
        .as_slice()
        .map_err(|_| value_error("values must be C-contiguous float64"))?;
    let result = py
        .allow_threads(|| temporal::interpolate(slice, shape[0], shape[1], factor))
        .map_err(value_error)?;
    Ok(result.into_pyarray(py))
}

#[pyfunction]
fn differential<'py>(
    py: Python<'py>,
    reference: PyReadonlyArray1<'py, f64>,
    comparison: PyReadonlyArray1<'py, f64>,
    mode: &str,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let r = reference
        .as_slice()
        .map_err(|_| value_error("reference must be contiguous"))?;
    let c = comparison
        .as_slice()
        .map_err(|_| value_error("comparison must be contiguous"))?;
    Ok(temporal::difference(r, c, mode)
        .map_err(value_error)?
        .into_pyarray(py))
}

#[pyfunction]
fn top_activity_indices(
    values: PyReadonlyArray2<'_, f64>,
    max_nodes: usize,
) -> PyResult<Vec<usize>> {
    let shape = values.shape();
    filter::top_activity(
        values
            .as_slice()
            .map_err(|_| value_error("values must be contiguous"))?,
        shape[0],
        shape[1],
        max_nodes,
    )
    .map_err(value_error)
}

#[pyfunction]
fn recommend_processing_mode(
    nodes: usize,
    edges: usize,
    frames: usize,
    bytes_per_value: usize,
    memory_limit: usize,
) -> &'static str {
    stats::recommend_mode(nodes, edges, frames, bytes_per_value, memory_limit)
}

#[pyfunction]
fn chunk_ranges(total: usize, chunk_size: usize) -> PyResult<Vec<(usize, usize)>> {
    streaming::chunk_ranges(total, chunk_size).map_err(value_error)
}

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyIndexedGraph>()?;
    module.add_function(wrap_pyfunction!(alignment_index, module)?)?;
    module.add_function(wrap_pyfunction!(normalize_matrix, module)?)?;
    module.add_function(wrap_pyfunction!(interpolate_matrix, module)?)?;
    module.add_function(wrap_pyfunction!(differential, module)?)?;
    module.add_function(wrap_pyfunction!(top_activity_indices, module)?)?;
    module.add_function(wrap_pyfunction!(recommend_processing_mode, module)?)?;
    module.add_function(wrap_pyfunction!(chunk_ranges, module)?)?;
    Ok(())
}
