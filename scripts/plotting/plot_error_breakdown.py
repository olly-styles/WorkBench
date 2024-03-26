import matplotlib.pyplot as plt

LABEL_DISTANCE = 1.2
CAPTION_FONTSIZE = 36

# Hard-coded results
correct = 0.42609
incorrrect_with_side_effects = 0.25652
incorrect_without_side_effects = 1 - correct - incorrrect_with_side_effects

# Plot a pie chart with adjusted title spacing
labels = ["Correct", "Side\nEffects", "No Side\nEffects"]
sizes = [correct, incorrrect_with_side_effects, incorrect_without_side_effects]
colors = ["gold", "lightcoral", "lightskyblue"]

fig, axs = plt.subplots(1, 3, figsize=(30, 6))  # Adjust figsize as needed to accommodate the charts

# increase font size
plt.rcParams.update({"font.size": 30})

# pie with label padding
axs[0].pie(
    sizes,
    labels=labels,
    colors=colors,
    autopct="%1.0f%%",
    startangle=70,
    wedgeprops=dict(edgecolor="black", linewidth=2),
    labeldistance=LABEL_DISTANCE,
    pctdistance=0.6,
    textprops={"fontsize": 24},
)
# plt.axis("equal")  # Ensure pie is drawn as a circle.
plt.text(
    0.5,
    -0.2,
    "(a) Overall Error Breakdown",
    horizontalalignment="center",
    verticalalignment="center",
    fontsize=CAPTION_FONTSIZE,
    transform=axs[0].transAxes,
)


# Hard-coded results
total = 57 + 28 + 8 + 15 + 46 + 65
failed_to_follow_react = 36 + 17 + 2 + 6 + 7 + 40
failed_to_retrive_email = 17 + 30 + 15
used_search_incorrectly = 3 + 11 + 7 + 1
other = total - failed_to_follow_react - failed_to_retrive_email - used_search_incorrectly

# Plot a pie chart for the errors with no side effects
labels = ["Failed to\nfollow ReAct", "Wrong\nemail", "Used search\nincorrectly", "Other"]

sizes = [failed_to_follow_react, failed_to_retrive_email, used_search_incorrectly, other]
# new set of colors that are all different from the previous ones
colors = ["lightgreen", "darkorange", "lightpink", "lightgrey"]
axs[1].pie(
    sizes,
    labels=labels,
    colors=colors,
    autopct="%1.0f%%",
    startangle=20,
    wedgeprops=dict(edgecolor="black", linewidth=2),
    labeldistance=LABEL_DISTANCE,
    pctdistance=0.6,
    textprops={"fontsize": 24},
)
plt.text(
    0.5,
    -0.2,
    "(b) Errors without Side Effects",
    horizontalalignment="center",
    verticalalignment="center",
    fontsize=CAPTION_FONTSIZE,
    transform=axs[1].transAxes,
)
# plt.axis("equal")
# tight layout
# plt.title("Errors with No Side Effects", pad=40, weight='bold')

# Errors with side effects

# Hard-coded results
total = 5 + 19 + 65 + 24 + 3 + 61
wrong_email = 17 + 5 + 12
updated_wrong_event = 16
misinterpreted_retrieved_data = 1 + 12 + 1 + 11
failed_to_identify_available_slot_in_calendar = 1 + 33
tried_to_plot_future_data = 44 + 1 + 1
other = (
    total
    - wrong_email
    - updated_wrong_event
    - misinterpreted_retrieved_data
    - failed_to_identify_available_slot_in_calendar
    - tried_to_plot_future_data
)

# Plot a pie chart for the errors with side effects
labels = [
    "Wrong\nemail",
    "Updated\nwrong event",
    "Misinterpreted\nretrieved data",
    "Failed to identify\navailable slot\nin calendar",
    "Tried to plot\nfuture data",
    "Other",
]
sizes = [
    wrong_email,
    updated_wrong_event,
    misinterpreted_retrieved_data,
    failed_to_identify_available_slot_in_calendar,
    tried_to_plot_future_data,
    other,
]

colors = ["darkorange", "lightyellow", "violet", "lightcyan", "greenyellow", "lightgrey"]
axs[2].pie(
    sizes,
    labels=labels,
    colors=colors,
    autopct="%1.0f%%",
    startangle=160,
    wedgeprops=dict(edgecolor="black", linewidth=2),
    labeldistance=LABEL_DISTANCE,
    pctdistance=0.6,
    textprops={"fontsize": 24},
)
plt.text(
    0.5,
    -0.2,
    "(c) Errors with Side Effects",
    horizontalalignment="center",
    verticalalignment="center",
    fontsize=CAPTION_FONTSIZE,
    transform=axs[2].transAxes,
)
# plt.axis("equal")
# tight layout
# plt.title("Errors with Side Effects", pad=40, weight='bold')
plt.savefig("data/plots/error_breakdown_all.png", bbox_inches="tight")  # Save the plot to a file
