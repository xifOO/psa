<!-- RULES:START -->

## 📋 Rules Reference

| ID | Rule | Group | Description | Config Parameter | Default Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LCOM001** | `LCOM_INCREASE` | Cohesion | Prohibits an increase in LCOM (degradation of cohesion) beyond the allowed delta. | `max_lcom_increase` | `0.2` |
| **LCOM002** | `HIGH_LCOM` | Cohesion | Limits the maximum absolute LCOM value for a class. | `max_lcom` | `WARNING` |
| **SE001** | `GLOBAL_WRITE` | Side Effects | Prohibits direct writes to global variables. | `max_global_writes` | `ERROR` |
| **SE002** | `ARG_MUTATION` | Side Effects | Limits the number of mutated function arguments. | `max_arg_mutations` | `WARNING` |
| **TCC001** | `TCC_INCREASE` | Cohesion | Prohibits a decrease in TCC (loss of cohesion) beyond the allowed delta. | `max_tcc_increase` | `ERROR` |
| **TCC002** | `HIGH_TCC` | Cohesion | Limits the maximum absolute TCC value for a class. | `max_tcc` | `WARNING` |

<!-- RULES:END -->
