pub fn top_activity(
    values: &[f64],
    rows: usize,
    cols: usize,
    max_nodes: usize,
) -> Result<Vec<usize>, String> {
    if rows.checked_mul(cols) != Some(values.len()) {
        return Err("invalid matrix dimensions".into());
    }
    let mut scores: Vec<(usize, f64)> = (0..cols)
        .map(|col| {
            let score = (0..rows)
                .map(|row| values[row * cols + col].abs())
                .filter(|v| v.is_finite())
                .fold(0.0, f64::max);
            (col, score)
        })
        .collect();
    scores.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(&b.0)));
    scores.truncate(max_nodes.min(cols));
    scores.sort_by_key(|pair| pair.0);
    Ok(scores.into_iter().map(|pair| pair.0).collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn selects_peak_activity() {
        assert_eq!(
            top_activity(&[1.0, 5.0, 2.0, 3.0], 2, 2, 1).unwrap(),
            vec![1]
        );
    }
}
