use std::collections::HashMap;

pub type AlignmentIndexResult = (Vec<i64>, Vec<String>, Vec<String>);

pub fn alignment_index(
    graph_ids: &[String],
    data_ids: &[String],
    policy: &str,
) -> Result<AlignmentIndexResult, String> {
    let mut lookup = HashMap::with_capacity(data_ids.len());
    for (idx, id) in data_ids.iter().enumerate() {
        if lookup.insert(id, idx as i64).is_some() {
            return Err(format!("duplicate data identifier: {id}"));
        }
    }
    let graph_set: std::collections::HashSet<&str> = graph_ids.iter().map(String::as_str).collect();
    let missing: Vec<String> = graph_ids
        .iter()
        .filter(|id| !lookup.contains_key(*id))
        .cloned()
        .collect();
    let extra: Vec<String> = data_ids
        .iter()
        .filter(|id| !graph_set.contains(id.as_str()))
        .cloned()
        .collect();
    if policy == "strict" && (!missing.is_empty() || !extra.is_empty()) {
        return Err(format!(
            "strict alignment failed; missing: [{}]; extra: [{}]",
            missing.join(", "),
            extra.join(", ")
        ));
    }
    if !matches!(policy, "strict" | "intersection" | "fill_missing") {
        return Err(format!("unknown alignment policy: {policy}"));
    }
    let indices = graph_ids
        .iter()
        .map(|id| lookup.get(id).copied().unwrap_or(-1))
        .collect();
    Ok((indices, missing, extra))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fill_missing_uses_sentinel() {
        let (index, missing, extra) = alignment_index(
            &["A".into(), "B".into()],
            &["B".into(), "C".into()],
            "fill_missing",
        )
        .unwrap();
        assert_eq!(index, vec![-1, 0]);
        assert_eq!(missing, vec!["A"]);
        assert_eq!(extra, vec!["C"]);
    }

    #[test]
    fn strict_reports_mismatch() {
        assert!(alignment_index(&["A".into()], &["B".into()], "strict").is_err());
    }
}
