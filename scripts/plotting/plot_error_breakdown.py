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
plt.rcParams.update({"font.size": 30})

plt.figure(figsize=(8, 6))  # Adjusting figure size for better layout
plt.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=-10)
plt.axis("equal")  # Ensure pie is drawn as a circle.

# Adjust title to prevent overlap
# bold title
# plt.title('Error Breakdown', pad=40, weight='bold')
# make sure labels are not cut off
plt.tight_layout()
plt.savefig("data/plots/error_breakdown.png", bbox_inches='tight')  # Save the plot to a file


total = 2 + 1 + 15 + 3 + 20
failed_to_follow_react = 2 + 9 + 1 + 4
failed_to_retrive_email = 1 + 5 + 16 
used_search_incorrectly = 1 + 2

assert total == failed_to_follow_react + failed_to_retrive_email + used_search_incorrectly

# Plot a pie chart for the errors with no side effects
labels = ["Failed to\nfollow ReAct", "Wrong\nemail", "Used search\nincorrectly"]

sizes = [failed_to_follow_react, failed_to_retrive_email, used_search_incorrectly]
# new set of colors that are all different from the previous ones
colors = ["lightgreen", "darkorange", "lightpink"]
plt.figure(figsize=(8, 6))
plt.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=20)
plt.axis("equal")
# tight layout
# plt.title("Errors with No Side Effects", pad=40, weight='bold')
plt.tight_layout()

plt.savefig("data/plots/error_breakdown_no_side_effects.png", bbox_inches='tight')  # Save the plot to a file

# Errors with side effects

total = 6 + 6 + 3 + 8
wrong_email = 6 + 1 + 8
updated_wrong_event = 4
partial_update = 1 + 3

assert total == wrong_email + updated_wrong_event + partial_update

# Plot a pie chart for the errors with side effects
labels = ["Wrong\nemail", "Updated wrong\nevent", "Partial\nupdate"]
sizes = [wrong_email, updated_wrong_event, partial_update]

colors = ["violet", "yellow", "lightblue"]
plt.figure(figsize=(8, 6))
plt.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=0)
plt.axis("equal")
# tight layout
# plt.title("Errors with Side Effects", pad=40, weight='bold')
plt.tight_layout()
plt.savefig("data/plots/error_breakdown_side_effects.png", bbox_inches='tight')  # Save the plot to a file