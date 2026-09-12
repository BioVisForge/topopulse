pub fn interpolate(
    values: &[f64],
    rows: usize,
    cols: usize,
    factor: usize,
) -> Result<Vec<f64>, String> {
    if rows.checked_mul(cols) != Some(values.len()) || factor == 0 {
        return Err("invalid interpolation dimensions or factor".into());
    }
    if rows <= 1 || factor == 1 {
        return Ok(values.to_vec());
    }
    let output_rows = (rows - 1) * factor + 1;
    let mut output = Vec::with_capacity(output_rows * cols);
    for row in 0..rows - 1 {
        for step in 0..factor {
            let alpha = step as f64 / factor as f64;
            for col in 0..cols {
                let left = values[row * cols + col];
                let right = values[(row + 1) * cols + col];
                output.push(if left.is_finite() && right.is_finite() {
                    left + alpha * (right - left)
                } else {
                    f64::NAN
                });
            }
        }
    }
    output.extend_from_slice(&values[(rows - 1) * cols..]);
    Ok(output)
}

pub fn difference(reference: &[f64], comparison: &[f64], mode: &str) -> Result<Vec<f64>, String> {
    if reference.len() != comparison.len() {
        return Err("reference and comparison shapes differ".into());
    }
    reference
        .iter()
        .zip(comparison)
        .map(|(&r, &c)| {
            if !r.is_finite() || !c.is_finite() {
                return Ok(f64::NAN);
            }
            match mode {
                "difference" => Ok(c - r),
                "ratio" => {
                    if r == 0.0 {
                        Ok(f64::NAN)
                    } else {
                        Ok(c / r)
                    }
                }
                "log2_fold_change" => {
                    if r <= 0.0 || c <= 0.0 {
                        Ok(f64::NAN)
                    } else {
                        Ok((c / r).log2())
                    }
                }
                "percent_change" => {
                    if r == 0.0 {
                        Ok(f64::NAN)
                    } else {
                        Ok(100.0 * (c - r) / r)
                    }
                }
                _ => Err(format!("unknown differential mode: {mode}")),
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn interpolation_preserves_endpoints() {
        assert_eq!(
            interpolate(&[0.0, 10.0], 2, 1, 2).unwrap(),
            vec![0.0, 5.0, 10.0]
        );
    }

    #[test]
    fn differences_are_correct() {
        assert_eq!(
            difference(&[1.0, 2.0], &[2.0, 1.0], "difference").unwrap(),
            vec![1.0, -1.0]
        );
        assert_eq!(
            difference(&[1.0], &[2.0], "percent_change").unwrap(),
            vec![100.0]
        );
    }
}
