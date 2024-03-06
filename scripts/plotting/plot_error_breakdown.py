import matplotlib.pyplot as plt

# Define the variables and repeat the plot with adjusted title spacing
correct = 0.5524
incorrrect_with_side_effects = 0.1608
incorrect_without_side_effects = 0.2868

# Plot a pie chart with adjusted title spacing
labels = ["Correct", "Side Effects", "No Side Effects"]
sizes = [correct, incorrrect_with_side_effects, incorrect_without_side_effects]
colors = ["gold", "lightcoral", "lightskyblue"]
# increase font size
plt.rcParams.update({"font.size": 20})

plt.figure(figsize=(8, 6))  # Adjusting figure size for better layout
plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=0)
plt.axis("equal")  # Ensure pie is drawn as a circle.

# Adjust title to prevent overlap
# plt.title('Error Breakdown', pad=20)  # pad adds space between the title and the plot
plt.savefig("data/plots/error_breakdown.png")  # Save the plot to a file
