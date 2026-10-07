"""Generate reproducible synthetic policies; no real corporate data is included."""
from pathlib import Path

from _common import ROOT
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

SAMPLES = {
    "employee_leave_policy.pdf": ("Employee leave policy", [
        [("Annual leave entitlement", "Employees at Northstar Labs receive 24 days of paid annual leave per calendar year. The leave year runs from January 1 to December 31. Public holidays are separate from the annual leave entitlement."),
         ("Carry-forward", "Employees may carry forward up to 5 unused annual leave days into the next calendar year. Carried days must be used by March 31. Additional carry-forward requires written approval from Human Resources.")],
        [("Requesting leave", "Submit a leave request through the HR portal at least 5 working days before the planned start date. The line manager approves or declines the request within 2 working days. Human Resources maintains the leave balance."),
         ("Urgent absence", "For an unexpected absence, notify the line manager before 10:00 AM on the first day whenever practical. Record the request in the HR portal when able. This policy does not specify parental leave or compensation rates.")],
    ]),
    "company_it_security_policy.pdf": ("Company IT security policy", [
        [("Password requirements", "Account passwords must contain at least 14 characters. Use a unique passphrase for every work account. Do not reuse personal passwords. Multi-factor authentication is mandatory for email, remote access and the HR portal."),
         ("Access approval", "The employee's line manager approves requests for business-system access. The IT Service Desk provisions approved access using the least-privilege principle. Shared accounts are prohibited.")],
        [("Security incidents", "The Security Operations team is responsible for triaging security incidents. Employees must report suspected incidents to the IT Service Desk within 30 minutes of discovery. Preserve suspicious messages and do not forward them to colleagues."),
         ("Document handling", "Store internal documents only in approved company storage. Do not send restricted documents to public AI services without explicit organizational authorization. Remove access promptly when an employee leaves the company.")],
    ]),
    "project_management_guidelines.pdf": ("Project management guidelines", [
        [("Project milestone stages", "Every project uses five milestone stages: initiation, planning, implementation, validation and closure. The project manager maintains the milestone register and assigns an owner to each deliverable."),
         ("Milestone approval", "The project sponsor approves milestone completion after reviewing the acceptance evidence. During validation, the quality lead records test outcomes and unresolved defects. A milestone cannot close with an unresolved critical defect.")],
        [("Delivery and reporting", "The project manager publishes a weekly status report each Friday. The report includes completed work, upcoming milestones, risks and decisions needed. Changes to scope require sponsor approval before implementation."),
         ("Leave and handover", "Team members planning leave must prepare a handover note listing active tasks, deadlines and backup owners. The line manager approves the leave request under the employee leave policy. The project manager updates the delivery plan.")],
    ]),
}


def generate(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Kicker", fontSize=9, textColor=colors.HexColor("#0D9488"), spaceAfter=18))
    styles.add(ParagraphStyle(name="PolicyTitle", fontSize=27, leading=32, textColor=colors.HexColor("#13243A"), spaceAfter=26))
    styles.add(ParagraphStyle(name="PolicyBody", fontSize=11, leading=18, alignment=TA_LEFT, spaceAfter=18))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(54, 48, 558, 48)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(54, 34, "NORTHSTAR LABS | Synthetic demonstration document | Version 1.0")
        canvas.drawRightString(558, 34, f"Page {doc.page}")
        canvas.restoreState()

    for filename, (title, pages) in SAMPLES.items():
        story = []
        for index, sections in enumerate(pages):
            if index:
                story.append(PageBreak())
            story += [Paragraph("NORTHSTAR LABS / PEOPLE & OPERATIONS", styles["Kicker"]),
                      Paragraph(title, styles["PolicyTitle"]),
                      Paragraph("Synthetic policy for the Document Intelligence project. Not a real company policy.", styles["PolicyBody"]),
                      Spacer(1, 0.15 * inch)]
            for heading, body in sections:
                story += [Paragraph(heading, styles["Heading2"]), Paragraph(body, styles["PolicyBody"])]
        SimpleDocTemplate(str(output / filename), pagesize=(612, 792), leftMargin=54, rightMargin=54,
                          topMargin=54, bottomMargin=66).build(story, onFirstPage=footer, onLaterPages=footer)
        print(output / filename)


if __name__ == "__main__":
    generate(ROOT / "data" / "sample_documents")
