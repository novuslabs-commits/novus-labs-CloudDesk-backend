import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.agent import Agent
from app.models.template import Template
from app.services.auth import hash_password
from app.services.template_matcher import template_matcher
import app.models

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- Agents ---
agents = [
    Agent(name="Admin User",   email="admin@clouddesk.com",   hashed_password=hash_password("Admin1234"),   role="admin",  team="Engineering",       is_active=True),
    Agent(name="Sara Khan",    email="sara@clouddesk.com",    hashed_password=hash_password("Agent1234"),   role="agent",  team="Billing",           is_active=True),
    Agent(name="Ali Hassan",   email="ali@clouddesk.com",     hashed_password=hash_password("Agent1234"),   role="agent",  team="Engineering",       is_active=True),
    Agent(name="Zara Ahmed",   email="zara@clouddesk.com",    hashed_password=hash_password("Agent1234"),   role="agent",  team="Product",           is_active=True),
    Agent(name="Omar Malik",   email="omar@clouddesk.com",    hashed_password=hash_password("Agent1234"),   role="agent",  team="Customer Success",  is_active=True),
    Agent(name="Hina Baig",    email="hina@clouddesk.com",    hashed_password=hash_password("Agent1234"),   role="agent",  team="Billing",           is_active=True),
]

for agent in agents:
    if not db.query(Agent).filter(Agent.email == agent.email).first():
        db.add(agent)

db.commit()
print(f"Agents seeded: {len(agents)}")

templates = [
    # ── BILLING ──────────────────────────────────────────────
    Template(intent="billing", title="Invoice Discrepancy",
             body="We completely understand how confusing it is to see an unexpected charge on your invoice. We've reviewed your account and can see the discrepancy — a relevant expert from our billing team will correct this and send you an updated invoice within 24 hours."),

    Template(intent="billing", title="Double Charge Resolution",
             body="That's definitely not right and we're sorry about that. We've confirmed the duplicate charge on our end and a refund for the extra amount has been initiated. You should see it back on your card within 3-5 business days — we've also added a note to make sure this doesn't happen again."),

    Template(intent="billing", title="Plan Downgrade Proration",
             body="We get it — plan changes and prorated amounts can be confusing. Your downgrade was processed correctly and the charge reflects only the prorated amount for the days you were on the higher plan. Your next invoice will show the new plan price in full — feel free to reach out if the numbers still don't add up."),

    Template(intent="billing", title="Missing Payment Receipt",
             body="No problem at all — we've resent your payment receipt to the email on your account. If you need it sent to a different address or need an official invoice for accounting purposes, just let us know and we'll get that sorted right away."),

    Template(intent="billing", title="Billing Cycle Question",
             body="Happy to clarify that. Your billing cycle renews on the same date each month based on when you first subscribed. You can view your full billing history and upcoming charges anytime under Settings → Billing in your dashboard. Let us know if anything there looks off."),

    Template(intent="billing", title="Failed Payment Retry",
             body="It looks like your recent payment didn't go through — this usually happens when a card has expired or the billing details have changed. You can update your payment method under Settings → Billing and we'll automatically retry the charge. Reach out if you run into any trouble."),

    Template(intent="billing", title="Annual Plan Charge Clarification",
             body="Annual plan charges can look larger than expected since they cover a full year upfront. The amount you were charged is correct for your current plan — you can see a full breakdown in your invoice under Settings → Billing. If you'd prefer to switch to monthly, we can help with that."),

    # ── TECHNICAL ────────────────────────────────────────────
    Template(intent="technical", title="Issue Under Investigation",
             body="We hear you and we're on it. Our engineering team has been looped in and is actively looking into this right now. We'll keep you updated every couple of hours until it's resolved — in the meantime, try clearing your cache and opening the app in an incognito window as a temporary workaround."),

    Template(intent="technical", title="Bug Confirmed and Fixed",
             body="Our team identified the root cause and deployed a fix. Please clear your browser cache, do a hard refresh, and try again — it should be working now. If you're still running into issues after 15 minutes, reply here and we'll dig deeper."),

    Template(intent="technical", title="Integration Troubleshooting",
             body="To help us track this down faster, could you share the exact error message or response code you're seeing, along with roughly when it started? Also helpful to know whether it's affecting all records or just specific ones. That'll get our team to the root cause much quicker."),

    Template(intent="technical", title="API Rate Limiting Issue",
             body="We've checked your account and can see the rate limiting isn't behaving as expected for your plan tier. This has been escalated to our infrastructure team as a priority — a relevant expert will follow up within 2 hours with an update and a resolution timeline."),

    Template(intent="technical", title="Performance Issue",
             body="Slow load times are frustrating and we understand the impact this has on your team. We're currently investigating a performance issue affecting some accounts — our team is actively working on it. We'll push an update as soon as we have more information."),

    Template(intent="technical", title="Data Export Issue",
             body="Export issues can be tricky — they're often tied to the size of the dataset or a specific filter combination. Could you let us know what date range and filters you're using when the export fails? That'll help our team reproduce and fix it quickly."),

    Template(intent="technical", title="Mobile App Crash",
             body="Sorry to hear the mobile app is giving you trouble. Could you let us know which device and OS version you're on, and what you were doing right before the crash? If you can share a screenshot of any error message that appeared, that would also help our team pinpoint the issue faster."),

    Template(intent="technical", title="Login or Authentication Error",
             body="Authentication errors like this are usually caused by a session conflict or a browser cache issue. Try clearing your cookies and cache, then log in fresh. If that doesn't work, try a different browser or device. If you're still blocked, reply here and we'll reset things from our end."),

    # ── FEATURE REQUEST ──────────────────────────────────────
    Template(intent="feature_request", title="Feature Request Logged",
             body="That's a genuinely useful idea — thank you for taking the time to share it. We've logged it in our product backlog and passed it along to the product team. We review feature requests during our quarterly planning and you'll hear from us if it makes it onto the roadmap."),

    Template(intent="feature_request", title="Feature Already on Roadmap",
             body="Great news — this is already something we're working on. We've added your account to the early access list so you'll be among the first to try it when it rolls out. We'll reach out as soon as it's available in your environment."),

    Template(intent="feature_request", title="Feature Under Consideration",
             body="We really appreciate this suggestion — it aligns with feedback we've been hearing from a few other teams as well. It's currently under active consideration by our product team. We can't promise a timeline just yet, but we'll make sure to loop you in if it moves forward."),

    Template(intent="feature_request", title="Workaround Available",
             body="We don't have that feature built in just yet, but there's a workaround that might help in the meantime. We've logged your request so the product team is aware of the demand. In the meantime, feel free to reply and we can walk you through the alternative approach."),

    Template(intent="feature_request", title="Feature Not Planned Currently",
             body="Thanks for the suggestion — we genuinely appreciate it. Honestly, this isn't something we have planned in the near term, but your feedback matters and we've added it to our backlog. If that changes, you'll be the first to know."),

    # ── COMPLAINT ────────────────────────────────────────────
    Template(intent="complaint", title="Sincere Apology with Escalation",
             body="We completely understand your frustration and we're sorry this has been your experience — it's not the standard we hold ourselves to. This has been escalated directly to our senior support manager who will personally reach out to you within 2 hours with a clear resolution plan."),

    Template(intent="complaint", title="Slow Response Acknowledgement",
             body="You're right to be frustrated — waiting this long for a response is unacceptable and we own that. A relevant expert from our team is now prioritising your case and will follow up with you personally within the next hour with a full update."),

    Template(intent="complaint", title="Agent Behaviour Complaint",
             body="We're really sorry to hear about your experience in that conversation — that's not how our team should be handling things. We take this seriously and will be reviewing that interaction internally. A senior team member will follow up with you directly today."),

    Template(intent="complaint", title="Repeated Issue Complaint",
             body="We hear you and we're sorry this keeps happening — dealing with the same issue more than once is genuinely unacceptable. We've flagged this as a recurring problem and a technical specialist will be personally assigned to your account to resolve it properly this time."),

    Template(intent="complaint", title="General Dissatisfaction",
             body="Thank you for being direct with us — we'd rather know than not. We're sorry the experience hasn't matched your expectations and we want to make it right. A relevant expert from our team will be in touch shortly to understand what's gone wrong and what we can do to fix it."),

    # ── REFUND ───────────────────────────────────────────────
    Template(intent="refund", title="Refund Approved",
             body="Your refund has been approved and processed. The amount will be returned to your original payment method within 5-7 business days depending on your bank. You'll get a confirmation email shortly — and if you don't see it within 7 days, just reach out."),

    Template(intent="refund", title="Refund Under Review",
             body="We've received your refund request and it's currently being reviewed by our billing team. We aim to get back to you within 1 business day. If approved, the refund will be processed within 5 business days from that point."),

    Template(intent="refund", title="Refund Outside Policy Window",
             body="We completely understand your frustration. Looking at your account, the cancellation falls outside our standard refund window, but we want to find a fair resolution. A member of our team will review your specific situation and follow up with you personally."),

    Template(intent="refund", title="Charged After Cancellation",
             body="That shouldn't have happened — we're sorry about that. We've confirmed the cancellation on our end and the post-cancellation charge is being refunded immediately. You should see it back within 3-5 business days. We've also made sure your account is fully closed."),

    Template(intent="refund", title="Partial Refund",
             body="After reviewing your account we've approved a partial refund covering the unused portion of your subscription. This has been initiated and will appear on your statement within 5-7 business days. Let us know if you have any questions about the calculation."),

    # ── ACCOUNT ACCESS ───────────────────────────────────────
    Template(intent="account_access", title="Password Reset Assistance",
             body="We've manually triggered a fresh password reset email to your registered address — please check your spam or junk folder if you don't see it within a few minutes. If it still doesn't come through, reply here and we'll reset access directly from our end after verifying your identity."),

    Template(intent="account_access", title="Account Unlocked",
             body="Your account has been unlocked. The lockout was most likely triggered by multiple failed login attempts which activated our security protection. You should be able to log in now with your existing credentials. As a precaution, you might want to reset your password via the login page."),

    Template(intent="account_access", title="Two Factor Authentication Issue",
             body="Getting locked out because of 2FA on a new device is frustrating — we get it. To restore access we'll need to verify your identity first. Please reply with the email address on the account and a recent invoice number or the last 4 digits of the card on file and we'll get you back in quickly."),

    Template(intent="account_access", title="Team Invitation Issue",
             body="The invitation email sometimes ends up in spam or gets blocked by corporate email filters. We've resent the invite from a different address — if it still doesn't arrive within 10 minutes, reply here and we'll manually add the team member to your workspace directly."),

    Template(intent="account_access", title="SSO Login Issue",
             body="SSO issues are usually caused by a configuration mismatch between your identity provider and our system. Could you let us know which SSO provider you're using and whether this is affecting all users or just specific ones? Our team will prioritise getting this resolved."),

    Template(intent="account_access", title="Account Suspended",
             body="It looks like your account was suspended due to a billing issue on our end — we're sorry for the disruption. Our billing team has been alerted and a relevant expert will follow up within the hour to restore access and resolve the underlying issue."),

    # ── GENERAL ──────────────────────────────────────────────
    Template(intent="general", title="General Acknowledgement",
             body="Thanks for reaching out — we've received your message and will make sure it gets to the right person. If there's anything specific you need help with in the meantime, feel free to ask and we'll get back to you as quickly as we can."),

    Template(intent="general", title="Positive Feedback Response",
             body="This genuinely made our day — thank you for taking the time to share this. We'll make sure to pass your kind words along to the team. It means a lot to know the work we're putting in is making a difference for you."),

    Template(intent="general", title="Data and Privacy Question",
             body="Great question — data privacy is something we take seriously. You can find our full data retention and privacy policy at clouddesk.com/privacy. If you need specific details for a compliance audit or have questions our policy page doesn't cover, reply here and we'll get you in touch with the right person."),

    Template(intent="general", title="Onboarding Question",
             body="Welcome aboard — happy to help you get set up. We have a getting started guide at help.clouddesk.com that covers the basics, and our onboarding team runs live sessions every Tuesday and Thursday if you'd prefer a walkthrough. Let us know what you need and we'll point you in the right direction."),

    Template(intent="general", title="Partnership or Sales Enquiry",
             body="Thanks for your interest in CloudDesk — we'd love to explore this further. The best next step is to connect you with the right person on our partnerships or sales team. Could you share a bit more about what you have in mind and we'll make the right introduction."),
]

for template in templates:
    db.add(template)

db.commit()
print(f"Templates seeded: {len(templates)}")

# refit template matcher with new templates
template_matcher.fit(db)
print(f"Template matcher fitted: {template_matcher.fitted}")

db.close()
print("\nSeed complete.")
print("Login credentials:")
print("  admin@clouddesk.com / Admin1234")
print("  sara@clouddesk.com  / Agent1234")
print("  ali@clouddesk.com   / Agent1234")