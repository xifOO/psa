## 📋 Rules Reference

| ID | Rule | Group | Description | Config Parameter | Default Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LCOM001** | `LCOM_INCREASE` | Cohesion | Запрещает рост LCOM (ухудшение связности) выше допустимой дельты. | `max_lcom_increased` | `ERROR` |
| **LCOM002** | `HIGH_LCOM` | Cohesion | Ограничивает максимальное абсолютное значение LCOM для класса. | `max_lcom` | `WARNING` |
| **SE001** | `GLOBAL_WRITE` | Side Effects | Запрещает прямую запись в глобальные переменные (global). | `max_global_writes` | `ERROR` |
| **SE002** | `ARG_MUTATION` | Side Effects | Ограничивает количество мутируемых аргументов функции. | `max_arg_mutations` | `WARNING` |
