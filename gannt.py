import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

# Tarefas com datas conhecidas
tasks = [
    ("REMOÇÕES", "2025-06-04", "2025-06-19"),
    ("DEMOLIÇÕES", "2025-06-04", "2025-07-19"),
    ("ALV. WEIS. (CHAPISCO + EMBOÇO)", "2025-06-30", "2025-07-18"),
    ("INST. HIDRO/SANIT.", "2025-07-14", "2025-07-18"),
    ("CHAPEO C/DPL/SPS.", "2025-07-21", "2025-07-27"),
    ("IMPERM. + PROT. MECÂNICA", "2025-07-24", "2025-07-28"),
    ("ELÉTRICA/EXAUSTÃO/AR COND. (BANHEIROS)", "2025-07-28", "2025-08-04"),
    ("BANHEIROS", "2025-08-04", "2025-08-07"),
    ("ANTI FERRUGEM", "2025-07-07", "2025-07-20"),
    ("REGULARIZAÇÃO / CONTRAPISO", "2025-07-21", "2025-08-05"),
    ("REFORÇO METÁLICO", "2025-08-06", "2025-08-20"),
]

# Tarefas sem data (vamos estimar)
estimated_tasks = [
    ("PISO + PAREDES", "2025-08-08", "2025-08-18"),
    ("FORRO", "2025-08-19", "2025-08-25"),
    ("DIVISÓRIAS (NEOCOM)", "2025-08-26", "2025-09-01"),
    ("CHAPISCO FUNDO LAJE", "2025-08-15", "2025-08-18"),
    ("INSTALAÇÕES", "2025-08-28", "2025-09-05"),     
    ("PISO GESSO", "2025-09-06", "2025-09-12"),
    ("DIVISÓRIAS", "2025-09-13", "2025-09-20"),
    ("DIVISÓRIAS VIDRO", "2025-09-21", "2025-09-28"),
]

# Combina tudo
all_tasks = tasks + estimated_tasks
df = pd.DataFrame(all_tasks, columns=["Tarefa", "Início", "Fim"])
df["Início"] = pd.to_datetime(df["Início"])
df["Fim"] = pd.to_datetime(df["Fim"])

# Gantt simples
fig, ax = plt.subplots(figsize=(12, 8))

for i, row in df.iterrows():
    ax.barh(y=i, width=(row["Fim"] - row["Início"]).days, left=row["Início"], align='center')
    ax.text(row["Início"], i, row["Tarefa"], va='center', ha='right', fontsize=9)

ax.set_yticks(range(len(df)))
ax.set_yticklabels([""] * len(df))  # Remove os rótulos duplicados
ax.invert_yaxis()
ax.xaxis_date()
plt.title("Cronograma Visual – Segundo Pavimento (Simples para Campo)")
plt.tight_layout()
plt.grid(axis='x', linestyle='--', alpha=0.5)
plt.xlabel("Data")
plt.show()
