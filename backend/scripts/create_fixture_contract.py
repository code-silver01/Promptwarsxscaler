# backend/scripts/create_fixture_contract.py
"""Generate a sample freelance agreement fixture for demo and testing."""
import os
from fpdf import FPDF  # pip install fpdf2

def create_sample_contract():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "FREELANCE SERVICES AGREEMENT", ln=True, align="C")
    pdf.ln(5)
    
    sections = [
        ("1. INTELLECTUAL PROPERTY TRANSFER", 
         "All work product, inventions, developments, improvements, and intellectual property rights "
         "conceived, developed, or reduced to practice by Contractor during the term of this Agreement, "
         "whether or not during working hours or using Company equipment, shall be and remain the exclusive "
         "property of Company. Contractor hereby irrevocably assigns all such rights to Company. "
         "Contractor waives any moral rights to such work product to the extent permitted by applicable law."),

        ("2. NON-COMPETE RESTRICTION",
         "For a period of twenty-four (24) months following the termination of this Agreement for any reason, "
         "Contractor shall not, directly or indirectly, engage in, consult for, or be employed by any person "
         "or entity that competes with Company's business anywhere in the world. This restriction applies "
         "regardless of whether Contractor is terminated with or without cause."),

        ("3. ARBITRATION AND DISPUTE RESOLUTION",
         "Any dispute, claim, or controversy arising out of or relating to this Agreement or the breach, "
         "termination, enforcement, interpretation, or validity thereof shall be resolved exclusively by "
         "binding arbitration before a single arbitrator. Contractor expressly and irrevocably waives the "
         "right to a jury trial and the right to participate in any class action or collective proceeding. "
         "Arbitration shall be conducted in Company's headquarters city at Contractor's expense."),

        ("4. AUTO-RENEWAL OF AGREEMENT",
         "This Agreement shall automatically renew for successive one-year terms unless either party provides "
         "written notice of non-renewal at least ninety (90) days prior to the end of the then-current term. "
         "Company reserves the right to adjust compensation rates upon renewal without prior notice. "
         "Failure to provide timely notice shall result in automatic binding renewal on current terms."),

        ("5. DATA COLLECTION AND USAGE",
         "Contractor acknowledges that Company may collect, retain, and use data about Contractor's work "
         "patterns, communications, and output for internal analytics and improvement purposes. Such data "
         "may be retained indefinitely and may be shared with Company's affiliates and service partners "
         "without further consent from Contractor."),

        ("6. PAYMENT AND LATE PENALTIES",
         "Invoices are due within 5 business days of receipt. Late payments shall incur a penalty of "
         "3% per month on the outstanding balance, compounded monthly. Failure to pay within 30 days "
         "shall constitute a material breach and entitle Company to terminate this Agreement and pursue "
         "all unpaid amounts plus collection costs and attorney's fees."),

        ("7. TERMINATION",
         "Company may terminate this Agreement immediately and without cause or notice at its sole "
         "discretion. Upon termination, Company shall pay only amounts earned through the termination date. "
         "Contractor shall have no recourse for wrongful termination or loss of anticipated future earnings."),

        ("8. INDEMNIFICATION",
         "Contractor shall indemnify, defend, and hold harmless Company from any and all third-party "
         "claims, damages, losses, liabilities, costs, and expenses, including reasonable attorney's fees, "
         "arising from Contractor's services, acts, or omissions under this Agreement, regardless of "
         "Company's contributory fault or negligence."),

        ("9. GOVERNING LAW",
         "This Agreement shall be governed exclusively by the laws of the State of Delaware. Any legal "
         "proceedings must be filed in the state or federal courts of New Castle County, Delaware, and "
         "Contractor irrevocably submits to the personal jurisdiction of such courts, waiving any "
         "objection based on venue or inconvenient forum."),

        ("10. MISCELLANEOUS",
         "This Agreement constitutes the entire agreement between the parties. Company may amend this "
         "Agreement at any time with reasonable notice. Continued performance by Contractor following "
         "any amendment constitutes acceptance of the modified terms."),
    ]

    for heading, text in sections:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, heading, ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, text)
        pdf.ln(4)

    os.makedirs("backend/tests/fixtures", exist_ok=True)
    pdf.output("backend/tests/fixtures/sample_contract.pdf")
    print("Created backend/tests/fixtures/sample_contract.pdf")

if __name__ == "__main__":
    create_sample_contract()
