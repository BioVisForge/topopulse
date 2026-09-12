pub fn recommend_mode(
    nodes: usize,
    edges: usize,
    frames: usize,
    bytes_per_value: usize,
    memory_limit: usize,
) -> &'static str {
    let data_bytes = frames
        .saturating_mul(nodes.saturating_add(edges))
        .saturating_mul(bytes_per_value);
    if data_bytes > memory_limit / 2 || edges > 1_000_000 || frames > 10_000 {
        "streaming"
    } else {
        "in_memory"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn recommends_streaming_for_large_data() {
        assert_eq!(
            recommend_mode(100_000, 1_000_000, 1_000, 8, 1_000_000),
            "streaming"
        );
        assert_eq!(recommend_mode(10, 10, 10, 8, 1_000_000), "in_memory");
    }
}
