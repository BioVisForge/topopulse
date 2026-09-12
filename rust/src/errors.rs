use pyo3::exceptions::PyValueError;
use pyo3::PyErr;

pub fn value_error(message: impl Into<String>) -> PyErr {
    PyValueError::new_err(message.into())
}
