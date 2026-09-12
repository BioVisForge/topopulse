use std::collections::{HashMap, HashSet, VecDeque};

#[derive(Debug, Clone)]
pub struct IndexedGraph {
    pub node_ids: Vec<String>,
    pub sources: Vec<u32>,
    pub targets: Vec<u32>,
    pub edge_types: Vec<String>,
    pub directed: bool,
}

impl IndexedGraph {
    pub fn build(
        source_ids: &[String],
        target_ids: &[String],
        edge_types: &[String],
        directed: bool,
    ) -> Result<Self, String> {
        if source_ids.len() != target_ids.len() {
            return Err("source and target arrays must have equal length".into());
        }
        if !edge_types.is_empty() && edge_types.len() != source_ids.len() {
            return Err("edge type array must be empty or match edge count".into());
        }
        let mut node_ids = Vec::new();
        let mut index = HashMap::<String, u32>::new();
        let intern = |id: &str, nodes: &mut Vec<String>, map: &mut HashMap<String, u32>| {
            if let Some(&idx) = map.get(id) {
                idx
            } else {
                let idx = nodes.len() as u32;
                nodes.push(id.to_owned());
                map.insert(id.to_owned(), idx);
                idx
            }
        };
        let mut sources = Vec::with_capacity(source_ids.len());
        let mut targets = Vec::with_capacity(target_ids.len());
        for (source, target) in source_ids.iter().zip(target_ids) {
            if source.is_empty() || target.is_empty() {
                return Err("node identifiers cannot be empty".into());
            }
            sources.push(intern(source, &mut node_ids, &mut index));
            targets.push(intern(target, &mut node_ids, &mut index));
        }
        let edge_types = if edge_types.is_empty() {
            vec!["unknown".into(); sources.len()]
        } else {
            edge_types.to_vec()
        };
        Ok(Self {
            node_ids,
            sources,
            targets,
            edge_types,
            directed,
        })
    }

    pub fn degrees(&self) -> Vec<u32> {
        let mut degrees = vec![0; self.node_ids.len()];
        for (&source, &target) in self.sources.iter().zip(&self.targets) {
            degrees[source as usize] += 1;
            degrees[target as usize] += 1;
        }
        degrees
    }

    pub fn component_labels(&self) -> Vec<u32> {
        let mut adjacency = vec![Vec::new(); self.node_ids.len()];
        for (&source, &target) in self.sources.iter().zip(&self.targets) {
            adjacency[source as usize].push(target as usize);
            adjacency[target as usize].push(source as usize);
        }
        let mut labels = vec![u32::MAX; self.node_ids.len()];
        let mut component = 0;
        for start in 0..self.node_ids.len() {
            if labels[start] != u32::MAX {
                continue;
            }
            labels[start] = component;
            let mut queue = VecDeque::from([start]);
            while let Some(node) = queue.pop_front() {
                for &neighbor in &adjacency[node] {
                    if labels[neighbor] == u32::MAX {
                        labels[neighbor] = component;
                        queue.push_back(neighbor);
                    }
                }
            }
            component += 1;
        }
        labels
    }

    pub fn duplicate_count(&self) -> usize {
        let mut seen = HashSet::new();
        self.sources
            .iter()
            .zip(&self.targets)
            .filter(|&(source, target)| !seen.insert((*source, *target)))
            .count()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stable_first_seen_indexing() {
        let g = IndexedGraph::build(
            &["B".into(), "A".into(), "B".into()],
            &["A".into(), "C".into(), "C".into()],
            &[],
            true,
        )
        .unwrap();
        assert_eq!(g.node_ids, vec!["B", "A", "C"]);
        assert_eq!(g.sources, vec![0, 1, 0]);
    }

    #[test]
    fn components_and_degrees() {
        let g = IndexedGraph::build(
            &["A".into(), "C".into()],
            &["B".into(), "D".into()],
            &[],
            true,
        )
        .unwrap();
        assert_eq!(g.degrees(), vec![1, 1, 1, 1]);
        assert_eq!(g.component_labels(), vec![0, 0, 1, 1]);
    }

    #[test]
    fn detects_duplicates() {
        let g = IndexedGraph::build(
            &["A".into(), "A".into()],
            &["B".into(), "B".into()],
            &[],
            true,
        )
        .unwrap();
        assert_eq!(g.duplicate_count(), 1);
    }
}
