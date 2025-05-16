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

# Melt the dataframe to long format for seaborn
melted = df.melt(id_vars='Time', 
                 value_vars=['Susceptible', 'Exposed', 'Believer', 'Doubter', 'Recovered', 'Disinformant'],
                 var_name='Agent Type', value_name='Count')

# Plot
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
plt.title('Agent Counts Over Time')
plt.tight_layout()
plt.show()