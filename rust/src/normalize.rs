fn finite_sorted(values: &[f64]) -> Vec<f64> {
    let mut finite: Vec<f64> = values.iter().copied().filter(|v| v.is_finite()).collect();
    finite.sort_by(f64::total_cmp);
    finite
}

fn quantile(sorted: &[f64], q: f64) -> f64 {
    if sorted.is_empty() {
        return f64::NAN;
    }
    let position = q.clamp(0.0, 1.0) * (sorted.len() - 1) as f64;
    let low = position.floor() as usize;
    let high = position.ceil() as usize;
    sorted[low] + (sorted[high] - sorted[low]) * (position - low as f64)
}

fn scale(value: f64, low: f64, high: f64) -> f64 {
    if !value.is_finite() {
        return f64::NAN;
    }
    if (high - low).abs() <= f64::EPSILON {
        return 0.5;
    }
    ((value - low) / (high - low)).clamp(0.0, 1.0)
}

pub fn normalize(
    values: &[f64],
    rows: usize,
    cols: usize,
    mode: &str,
    params: &[f64],
) -> Result<Vec<f64>, String> {
    if rows.checked_mul(cols) != Some(values.len()) {
        return Err("rows * cols must match value count".into());
    }
    match mode {
        "global" => {
            let finite = finite_sorted(values);
            let low = finite.first().copied().unwrap_or(f64::NAN);
            let high = finite.last().copied().unwrap_or(f64::NAN);
            Ok(values.iter().map(|&v| scale(v, low, high)).collect())
        }
        "per_frame" => {
            let mut output = Vec::with_capacity(values.len());
            for row in values.chunks(cols) {
                let finite = finite_sorted(row);
                let low = finite.first().copied().unwrap_or(f64::NAN);
                let high = finite.last().copied().unwrap_or(f64::NAN);
                output.extend(row.iter().map(|&v| scale(v, low, high)));
            }
            Ok(output)
        }
        "fixed" => {
            if params.len() != 2 || params[0] >= params[1] {
                return Err("fixed normalization requires min < max".into());
            }
            Ok(values
                .iter()
                .map(|&v| scale(v, params[0], params[1]))
                .collect())
        }
        "symmetric" => {
            let max_abs = values
                .iter()
                .copied()
                .filter(|v| v.is_finite())
                .map(f64::abs)
                .fold(0.0, f64::max);
            Ok(values
                .iter()
                .map(|&v| scale(v, -max_abs, max_abs))
                .collect())
        }
        "percentile" => {
            let (low_q, high_q) = if params.len() == 2 {
                (params[0], params[1])
            } else {
                (0.02, 0.98)
            };
            let finite = finite_sorted(values);
            let low = quantile(&finite, low_q);
            let high = quantile(&finite, high_q);
            Ok(values.iter().map(|&v| scale(v, low, high)).collect())
        }
        "zscore" => {
            let finite = finite_sorted(values);
            let mean = finite.iter().sum::<f64>() / finite.len().max(1) as f64;
            let variance =
                finite.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / finite.len().max(1) as f64;
            let sd = variance.sqrt();
            Ok(values
                .iter()
                .map(|&v| {
                    if v.is_finite() && sd > 0.0 {
                        (v - mean) / sd
                    } else if v.is_finite() {
                        0.0
                    } else {
                        f64::NAN
                    }
                })
                .collect())
        }
        "robust_zscore" => {
            let finite = finite_sorted(values);
            let median = quantile(&finite, 0.5);
            let q1 = quantile(&finite, 0.25);
            let q3 = quantile(&finite, 0.75);
            let iqr = q3 - q1;
            Ok(values
                .iter()
                .map(|&v| {
                    if v.is_finite() && iqr > 0.0 {
                        (v - median) / iqr
                    } else if v.is_finite() {
                        0.0
                    } else {
                        f64::NAN
                    }
                })
                .collect())
        }
        "log" => Ok(values
            .iter()
            .map(|&v| if v > 0.0 { v.ln() } else { f64::NAN })
            .collect()),
        "log1p" => Ok(values
            .iter()
            .map(|&v| if v >= -1.0 { v.ln_1p() } else { f64::NAN })
            .collect()),
        _ => Err(format!("unknown normalization mode: {mode}")),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn global_and_missing() {
        assert_eq!(
            normalize(&[0.0, 5.0, 10.0, f64::NAN], 2, 2, "global", &[]).unwrap()[0..3],
            [0.0, 0.5, 1.0]
        );
        assert!(normalize(&[0.0, f64::NAN], 1, 2, "global", &[]).unwrap()[1].is_nan());
    }

    #[test]
    fn per_frame_changes_scale() {
        assert_eq!(
            normalize(&[0.0, 1.0, 10.0, 20.0], 2, 2, "per_frame", &[]).unwrap(),
            vec![0.0, 1.0, 0.0, 1.0]
        );
    }

    #[test]
    fn symmetric_centers_zero() {
        let got = normalize(&[-2.0, 0.0, 1.0], 1, 3, "symmetric", &[]).unwrap();
        assert_relative_eq!(got[1], 0.5);
    }

    #[test]
    fn global_is_bounded_across_deterministic_range() {
        let values: Vec<f64> = (-100..=100).map(|value| value as f64 * 997.3).collect();
        let got = normalize(&values, 1, values.len(), "global", &[]).unwrap();
        assert!(got.iter().all(|value| (0.0..=1.0).contains(value)));
    }
}
