## Rules Reference

| ID | Rule | Group | Description | Config Parameter | Default Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LCOM001** | `LCOM_INCREASE` | Cohesion | Prohibits an increase in LCOM (degradation of cohesion) beyond the allowed delta. | `max_lcom_increased` | `ERROR` |
| **LCOM002** | `HIGH_LCOM` | Cohesion | Limits the maximum absolute LCOM value for a class. | `max_lcom` | `WARNING` |
| **SE001** | `GLOBAL_WRITE` | Side Effects | Prohibits direct writes to global variables. | `max_global_writes` | `ERROR` |
| **SE002** | `ARG_MUTATION` | Side Effects | Limits the number of mutated function arguments. | `max_arg_mutations` | `WARNING` |
