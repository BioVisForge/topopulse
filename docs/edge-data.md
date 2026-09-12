# Edge data

Wide edge tables use identifiers such as `EGFR|RAS`. Long form uses
`time,source,target,value`. Every edge is aligned explicitly to the graph.

Set `EdgeStyle(direction="flux")` when a negative value should reverse the drawn arrow. Signed
confidence or influence values do not reverse direction under the default `network` policy.

