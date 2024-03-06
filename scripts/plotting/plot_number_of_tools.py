# Re-import necessary libraries after reset
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Data preparation
domains = ["Multi\nDomain", "Email", "Calendar", "Analytics", "Project\nManagement", "CRM", "Overall"]
accuracy_all_tools = [61.9, 59.26, 76.67, 100.0, 23.08, 25.0, 55.24]
accuracy_single_tool = [66.67, 51.85, 63.33, 93.33, 30.77, 33.33, 53.85]
data = {
    "Domain": domains * 2,
    "Accuracy (%)": accuracy_single_tool + accuracy_all_tools,
    "Run Type": ["Single tool"] * len(domains) + ["All tools"] * len(domains),
}

# Convert dictionary to DataFrame
df = pd.DataFrame(data)

# Increase font size
sns.set(font_scale=2.2)

# Set up the seaborn plot
plt.figure(figsize=(14, 8))
sns.barplot(x="Domain", y="Accuracy (%)", hue="Run Type", data=df, palette="coolwarm")


plt.title("Comparison of Accuracy Between Single-Tool and All-Tools Runs")
plt.tight_layout()

plt.savefig("data/plots/number_of_tools_accuracy_comparison.png")
