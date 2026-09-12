pub fn chunk_ranges(total: usize, chunk_size: usize) -> Result<Vec<(usize, usize)>, String> {
    if chunk_size == 0 {
        return Err("chunk_size must be positive".into());
    }
    Ok((0..total)
        .step_by(chunk_size)
        .map(|start| (start, (start + chunk_size).min(total)))
        .collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn final_chunk_is_bounded() {
        assert_eq!(chunk_ranges(5, 2).unwrap(), vec![(0, 2), (2, 4), (4, 5)]);
    }
}
