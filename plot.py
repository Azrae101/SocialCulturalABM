import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load the CSV log
df = pd.read_csv('simulation_log.csv')

# Convert 'Time' to a string (if not already)
df['Time'] = df['Time'].astype(str)

# Set the plot style
sns.set(style="whitegrid")

# Define custom colors to match main.py
agent_palette = {
    'Susceptible': '#6aa84f',    # (106, 168, 79)
    'Exposed': '#ffff00',        # (255, 255, 0)
    'Believer': '#cc0000',       # (204, 0, 0)
    'Doubter': '#3d85c6',        # (61, 133, 198)
    'Recovered': '#808080',      # (128, 128, 128)
    'Disinformant': '#b400b4',   # (180, 0, 180)
}

agent_types = ['Susceptible', 'Exposed', 'Believer', 'Doubter', 'Recovered', 'Disinformant']

# Melt the dataframe to long format for seaborn
melted = df.melt(id_vars='Time', 
                 value_vars=agent_types,
                 var_name='Agent Type', value_name='Count')

# --- 1. Line Plot (original) ---
plt.figure(figsize=(14, 7))
sns.lineplot(
    data=melted, 
    x='Time', 
    y='Count', 
    hue='Agent Type', 
    marker='o',
    palette=agent_palette
)
plt.xticks(rotation=45, fontsize=8)
plt.title('Agent Counts Over Time (Line Plot)')
plt.tight_layout()
plt.show()

# --- 2. Stacked Area Plot ---
plt.figure(figsize=(14, 7))
plt.stackplot(
    df['Time'],
    [df[atype] for atype in agent_types],
    labels=agent_types,
    colors=[agent_palette[atype] for atype in agent_types]
)
plt.legend(loc='upper right')
plt.xticks(rotation=45, fontsize=8)
plt.title('Agent Counts Over Time (Stacked Area Plot)')
plt.tight_layout()
plt.show()

# --- 3. Proportion Stacked Area Plot ---
df_prop = df.copy()
total = df_prop[agent_types].sum(axis=1)
for atype in agent_types:
    df_prop[atype] = df_prop[atype] / total

plt.figure(figsize=(14, 7))
plt.stackplot(
    df_prop['Time'],
    [df_prop[atype] for atype in agent_types],
    labels=agent_types,
    colors=[agent_palette[atype] for atype in agent_types]
)
plt.legend(loc='upper right')
plt.xticks(rotation=45, fontsize=8)
plt.title('Agent Proportions Over Time (Stacked Area Plot)')
plt.tight_layout()
plt.show()

# --- 4. FacetGrid (Small Multiples) ---
g = sns.FacetGrid(melted, col="Agent Type", col_wrap=3, sharey=False, height=3.5, aspect=1.5, palette=agent_palette)
g.map_dataframe(sns.lineplot, x="Time", y="Count", color=None)
g.set_titles("{col_name}")
for ax, atype in zip(g.axes.flat, agent_types):
    ax.set_facecolor('white')
    ax.lines[0].set_color(agent_palette[atype])
    ax.tick_params(axis='x', rotation=45)
g.fig.suptitle('Agent Counts Over Time (FacetGrid)', y=1.02)
plt.tight_layout()
plt.show()

# --- 5. Heatmap ---
heatmap_data = df[agent_types].T
plt.figure(figsize=(12, 4))
sns.heatmap(heatmap_data, cmap="YlGnBu", cbar_kws={'label': 'Agent Count'}, xticklabels=df['Time'])
plt.yticks(rotation=0)
plt.title('Agent Counts Over Time (Heatmap)')
plt.xlabel('Time')
plt.tight_layout()
plt.show()