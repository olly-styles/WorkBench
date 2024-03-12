# Re-import necessary libraries after reset
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Data preparation
domains = ["Multi\nDomain (21)\n", "Email (27)\n", "Calendar (30)\n", "Analytics (15)\n", "Project\nManagement (26)\n", "CRM (24)\n", "Overall (143)\n"]
accuracy_all_tools = [61.9, 59.26, 76.67, 100.0, 23.08, 25.0, 55.24]
accuracy_single_tool = [66.67, 51.85, 63.33, 93.33, 30.77, 33.33, 53.85]

domains = ["Analytics\n(15)\n", "CRM\n(24)\n", "Calendar\n(30)\n", "Email\n(27)\n", "Project\nManagement\n(26)\n", "Multi\nDomain\n(21)\n", "Overall\n(143)\n"]
accuracy_all_tools = [100.0, 25.0, 76.67, 59.26, 23.08, 61.9, 55.24]
accuracy_single_tool = [93.33, 33.33, 63.33, 51.85, 30.77, 66.67, 53.85]


data = {
    "Domain": domains * 2,
    "Accuracy (%)": accuracy_single_tool + accuracy_all_tools,
    "Run Type": ["Required Toolkit"] * len(domains) + ["All Toolkits"] * len(domains),
}

# Convert dictionary to DataFrame
df = pd.DataFrame(data)

# Increase font size
sns.set(font_scale=2.5)

# Set up the seaborn plot
plt.figure(figsize=(18, 8))
sns.barplot(x="Domain", y="Accuracy (%)", hue="Run Type", data=df, palette="coolwarm")
# remove heading from key
plt.legend(title=None)
# make x and y labels bold
plt.xlabel("Domain", weight="bold")
plt.ylabel("Accuracy (%)", weight="bold")


# plt.title("Comparison of Accuracy Between Providing on Toolkit vs All Toolkits")
plt.tight_layout()

plt.savefig("data/plots/number_of_tools_accuracy_comparison.png")
