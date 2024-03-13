import random
import csv 
import pandas as pd

tasks = [
    "Add animation to carousel",
    "Add authentication for email notification",
    "Update Flask to latest version",
    "Optimize database query for search functionality",
    "Add authentication for third-party login",
    "Fix alignment issue in homepage",
    "Add animation to form submission button",
    "Fix alignment issue in settings page",
    "Implement responsive layout for profile page",
    "Fix alignment issue in profile page",
    "Add animation to form submission button",
    "Update brand colors in website",
    "Design logo for e-commerce platform",
    "Develop prototype for payment gateway",
    "Design logo for blog",
    "Design logo for website",
    "Create wireframe for homepage",
    "Develop prototype for login system",
    "Fix bug in user management module",
    "Optimize database query for user management",
    "Improve UX of onboarding process",
    "Update Django to latest version",
    "Fix bug in content delivery module",
    "Implement report generation API",
    "Add animation to form submission button",
    "Fix alignment issue in homepage",
    "Update react to latest version",
    "Design UI for landing page",
    "Add authentication for email notification",
    "Add authentication for cloud storage",
    "Design UI for settings page",
    "Develop prototype for login system",
    "Implement user profile management API",
    "Develop prototype for report generation",
    "Optimize database query for report generation",
    "Improve UX of feedback submission",
    "Design logo for website",
    "Develop prototype for payment gateway",
    "Implement payment gateway API",
    "Integrate Google Maps API with frontend",
    "Design UI for landing page",
    "Implement report generation API",
    "Design logo for admin panel",
    "Implement user profile management API",
    "Optimize database query for user management",
    "Add authentication for third-party login",
    "Update brand colors in e-commerce platform",
    "Add authentication for third-party login",
    "Fix alignment issue in homepage"
]
events = pd.read_csv("data/raw/events.csv", header=None)[0].tolist()

greetings = ["Hi Sam,", "Hey Sam,", "Dear Sam,", "Sam,"]
senders = ["Aisha", "Carlos", "Fatima", "Dmitri", "Yuki", "Nia", "Leila", "Santiago", "Chenwei", 
           "Anaya", "Kofi", "Luis", "Olga", "Jinsoo", "Amir", "Lena", "Raj", "Sofia", "Akira", "Nadia"]

# Update generate_email_content to include both events and tasks
def generate_email_content_updated(sender, event, is_long=False, task=None, contains_typo=False):
    bodies_event = [
        f"I'm reaching out to discuss our upcoming {event}. Can we schedule a meeting to go over the details?",
        f"I wanted to let you know that I've completed the tasks for the {event}. Looking forward to your feedback.",
        f"Could you provide your input on the {event} planning? Your insights would be really valuable.",
        f"Reminder about the {event} next week. Let's make sure we're all prepared.",
        f"I have some ideas for the {event} that I'd like to run by you. When are you free?",
        f"Encountered a few challenges while working on the {event}. Could use your advice.",
        f"Thanks for the invite. Looking forward to it!"
    ]
    bodies_task = [
        f"Regarding task '{task}', I've made significant progress but have hit a snag with {random.choice(['database integration', 'UI responsiveness', 'third-party API compatibility'])}. Could use a brainstorm session.",
        f"Completed task '{task}' ahead of schedule. Please review and let me know if any tweaks are needed.",
        f"Starting on '{task}' today. Any preliminary thoughts or resources you recommend before I dive in?",
        f"I've been assigned '{task}'. Excited to work on this and confident it will greatly improve our {random.choice(['user experience', 'backend efficiency', 'security protocols'])}."
    ]
    closings = ["Best,", "Regards,", "Cheers,", "Thanks,"]

    if is_long:
        additional_content = ["\n\nAdditionally, I wanted to touch base on some other areas we've been focusing on lately. Our team has been working tirelessly on improving our project management workflows and enhancing collaboration across departments. This effort includes adopting new tools, refining our communication strategies, and ensuring that all team members are fully aligned with our objectives.",
                              "\n\nI also wanted to share some exciting news about our upcoming team-building event. We've been planning a fun and engaging day for everyone, and I'm confident it will be a great opportunity for everyone to unwind and bond with their colleagues. I'll be sending out more details soon, so keep an eye out for that!",
                              "\n\nI've been meaning to discuss the recent changes in our project timelines. We've had to make some adjustments to accommodate new client requirements and to ensure that we're delivering the best possible results. I'll be reaching out to you soon to discuss this in more detail, so please keep an eye out for my next email."]
        body = f"{random.choice(greetings)}\n\n{random.choice(bodies_task if task else bodies_event)}{random.choice(additional_content) if is_long else ''}\n\n{random.choice(closings)}\n{sender}"
    else:
        body = f"{random.choice(greetings)}\n\n{random.choice(bodies_task if task else bodies_event)}\n\n{random.choice(closings)}\n{sender}"
    possible_typos = [["I've", "Iv"], ["significant", "signficant"], ["ahead", "ahed"], ["recommend", "reccomend"], ["efficiency", "efficency"], ["Additionally", "Additionnally"], ["regarding", "reguarding"], ["alignment", "alignement"], ["collaboration", "collabaration"], ["communication", "comunication"], ["objective", "objectif"], ["recent", "recentt"], ["accommodate", "acommodate"], ["unwind", "unwindd"], ["bond", "bondd"], ["upcoming", "upcomming"], ["planning", "planing"], ["engaging", "engagging"], ["opportunity", "oppurtunity"], ["unwind", "unwindd"], ["recent", "recennt"], ["adjustments", "adjusments"], ["invite", "invit"], ["forward", "foward"], ["ideas", "idaes"], ["Let's", "lets"], ["we're", "Were"], ["advice", "advise"]]
    if contains_typo:
        typos_in_body = [typo for typo in possible_typos if typo[0] in body]
        typo = random.choice(typos_in_body)
        body = body.replace(typo[0], typo[1])

    return body

# Update the CSV file generation with these improvements
filename_updated = "data/raw/email_content_pairs.csv"

with open(filename_updated, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Subject", "Content"])

    for i in range(500):
        sender = random.choice(senders)
        if i % 2 == 0:  # Alternate between events and tasks
            event = random.choice(events)
            subject = f"Update on {event}"
            content = generate_email_content_updated(sender, event, is_long=(i % 5 == 0), contains_typo=(i % 5 == 0))
        else:
            task = random.choice(tasks)
            subject = f"Task Update on {task}"
            content = generate_email_content_updated(sender, event=None, is_long=(i % 5 == 0), task=task, contains_typo=(i % 5 == 0))
        writer.writerow([subject, content])
