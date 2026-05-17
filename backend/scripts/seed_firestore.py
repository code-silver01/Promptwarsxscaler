"""
Seed script for LexGuard One Firestore benchmark corpus.
Run once: python -m backend.scripts.seed_firestore
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

BENCHMARK_CLAUSES = [
    # IP_TRANSFER — exploitative (risk_level=HIGH, is_user_favorable=False)
    {
        "category": "IP_TRANSFER",
        "text": "All inventions, discoveries, developments, and works of authorship conceived, developed, or reduced to practice by Employee during the term of employment, whether or not during working hours or using Company resources, shall be the exclusive property of the Company.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "IP_TRANSFER",
        "text": "Employee irrevocably assigns to Company all intellectual property rights in any work created in connection with the services provided, including moral rights to the extent permitted by law.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "IP_TRANSFER",
        "text": "Any work product, invention, or intellectual property developed using Company equipment or during Company time is the exclusive property of Company. Employee retains rights to inventions developed entirely on personal time without Company resources and unrelated to Company business.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # IP_TRANSFER — fair (is_user_favorable=True)
    {
        "category": "IP_TRANSFER",
        "text": "Intellectual property created solely by Employee on personal time, using personal resources, and unrelated to Company's current or reasonably anticipated business, products, or research shall remain the sole property of Employee.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "IP_TRANSFER",
        "text": "Company claims ownership only of work product created during working hours using Company-provided resources. Employee retains all rights to prior inventions listed in Exhibit A.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "IP_TRANSFER",
        "text": "Ownership of intellectual property shall be determined by applicable copyright and patent law. Employee retains rights to work created outside of employment scope.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # NON_COMPETE — exploitative
    {
        "category": "NON_COMPETE",
        "text": "For a period of 24 months following termination of employment for any reason, Employee shall not, directly or indirectly, engage in, own, manage, operate, consult for, or be employed by any business that competes with Company anywhere in the world.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "NON_COMPETE",
        "text": "Employee agrees not to work for any competitor, as solely determined by Company, for 18 months post-termination within a 200-mile radius.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "NON_COMPETE",
        "text": "Employee shall not solicit Company clients or employees for 12 months after termination, within the geographic territory Employee served.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # NON_COMPETE — fair
    {
        "category": "NON_COMPETE",
        "text": "Employee agrees not to directly solicit Company's named clients for a period of 6 months following voluntary resignation. This restriction does not apply upon termination by Company.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "NON_COMPETE",
        "text": "Non-compete restrictions are limited to direct competitors in Employee's specific product area and apply only within Employee's assigned sales territory for a maximum of 6 months.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "NON_COMPETE",
        "text": "Employee may work for competitors after employment ends, provided Employee does not use or disclose Company confidential information.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # ARBITRATION — exploitative
    {
        "category": "ARBITRATION",
        "text": "Any and all disputes arising out of or relating to this Agreement shall be resolved exclusively by binding arbitration administered by the American Arbitration Association. Employee expressly waives the right to a jury trial or class action.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "ARBITRATION",
        "text": "All claims, including discrimination and wage claims, must be submitted to private arbitration. Employee waives the right to bring or participate in any class or collective action.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "ARBITRATION",
        "text": "Disputes shall be resolved by arbitration in Company's headquarters city, with costs split equally between the parties.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # ARBITRATION — fair
    {
        "category": "ARBITRATION",
        "text": "Either party may elect arbitration for disputes over $5,000. For smaller claims, Employee retains the right to file in small claims court. Class actions are not waived.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "ARBITRATION",
        "text": "Arbitration is available as an optional dispute resolution mechanism. Nothing in this agreement prevents Employee from filing claims with government agencies such as the EEOC or NLRB.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "ARBITRATION",
        "text": "If arbitration is elected, costs shall be borne by Company. Employee retains the right to seek injunctive relief in any court of competent jurisdiction.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # AUTO_RENEWAL — exploitative
    {
        "category": "AUTO_RENEWAL",
        "text": "This Agreement shall automatically renew for successive one-year terms unless either party provides written notice of non-renewal at least 90 days prior to the end of the then-current term.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "AUTO_RENEWAL",
        "text": "Subscription automatically renews annually at the then-current rate. Cancellation requires 60 days written notice before renewal date. No refunds for partial periods.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "AUTO_RENEWAL",
        "text": "Service renews monthly unless cancelled 30 days in advance. Company may adjust pricing upon renewal with 30 days notice.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # AUTO_RENEWAL — fair
    {
        "category": "AUTO_RENEWAL",
        "text": "Subscription renews monthly. User may cancel at any time with effect from end of current billing period. Company will send a renewal reminder 14 days before each renewal date.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "AUTO_RENEWAL",
        "text": "This agreement renews annually. If Company changes pricing, User may cancel within 30 days of notice without penalty and receive a pro-rated refund.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "AUTO_RENEWAL",
        "text": "Auto-renewal requires affirmative opt-in confirmation from User each term. No automatic charges without explicit consent.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # LIABILITY_LIMITATION — exploitative
    {
        "category": "LIABILITY_LIMITATION",
        "text": "IN NO EVENT SHALL COMPANY BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES. COMPANY'S TOTAL LIABILITY SHALL NOT EXCEED ONE HUNDRED DOLLARS ($100).",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "LIABILITY_LIMITATION",
        "text": "Company's total cumulative liability for any and all claims shall not exceed the fees paid by User in the three months preceding the claim.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    {
        "category": "LIABILITY_LIMITATION",
        "text": "Company expressly disclaims all warranties, express or implied. Use of the service is at User's sole risk.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    # LIABILITY_LIMITATION — fair
    {
        "category": "LIABILITY_LIMITATION",
        "text": "Liability limitations do not apply to damages arising from gross negligence, willful misconduct, death, or personal injury caused by Company.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "LIABILITY_LIMITATION",
        "text": "Company's liability cap shall not apply to breaches of confidentiality obligations or intellectual property indemnification.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "LIABILITY_LIMITATION",
        "text": "Company's liability is limited to fees paid in the prior 12 months. This limitation does not apply to data breaches caused by Company's negligence.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # DATA_COLLECTION — exploitative
    {
        "category": "DATA_COLLECTION",
        "text": "By using this service, you consent to the collection, processing, and sharing of your personal data with our partners and affiliates for marketing, analytics, and product improvement purposes without further notice.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "DATA_COLLECTION",
        "text": "Company may collect, retain, and sell anonymized or aggregated user data to third parties. User data may be retained indefinitely.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "DATA_COLLECTION",
        "text": "Company collects usage analytics and may share de-identified data with third-party analytics providers. User may opt out of marketing emails.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # DATA_COLLECTION — fair
    {
        "category": "DATA_COLLECTION",
        "text": "Company collects only data necessary to provide the service. Data is not sold to third parties. User may request deletion of all personal data at any time under applicable privacy law.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "DATA_COLLECTION",
        "text": "User data is retained for 12 months following account closure and then permanently deleted. User may export all personal data in machine-readable format upon request.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "DATA_COLLECTION",
        "text": "Data sharing with third parties requires separate explicit consent. Company will not process personal data for purposes beyond the original collection purpose without User consent.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # TERMINATION — exploitative
    {
        "category": "TERMINATION",
        "text": "Company may terminate this Agreement immediately and without cause, notice, or compensation at its sole discretion. Employee shall have no recourse for wrongful termination.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "TERMINATION",
        "text": "Company reserves the right to terminate Employee's access to all systems and remove Employee from premises immediately upon notice of termination, regardless of cause.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    {
        "category": "TERMINATION",
        "text": "Company may terminate this agreement with 7 days written notice. Employee may terminate with 30 days written notice.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # TERMINATION — fair
    {
        "category": "TERMINATION",
        "text": "Either party may terminate this Agreement with 30 days written notice. In the event of termination without cause by Company, Employee shall receive severance equal to one month's salary per year of service.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "TERMINATION",
        "text": "Termination for cause requires a written notice specifying the breach and a 10-day cure period before termination becomes effective.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "TERMINATION",
        "text": "Both parties have equal termination rights with 30 days notice. Company shall pay all accrued but unpaid compensation within 3 business days of termination.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # PAYMENT_PENALTY — exploitative
    {
        "category": "PAYMENT_PENALTY",
        "text": "Late payments shall incur a penalty of 5% per month on the outstanding balance, compounded monthly, plus all costs of collection including attorney's fees.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "PAYMENT_PENALTY",
        "text": "Failure to pay any invoice within 5 business days of due date shall constitute a material breach entitling Company to terminate the Agreement and demand immediate payment of all future amounts.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "PAYMENT_PENALTY",
        "text": "Payments more than 15 days late will incur a 2% monthly late fee. Service may be suspended after 30 days of non-payment.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    # PAYMENT_PENALTY — fair
    {
        "category": "PAYMENT_PENALTY",
        "text": "Late payments are subject to a maximum interest rate of 1.5% per annum above the prevailing bank rate. No penalties apply for payments delayed due to a bona fide dispute.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "PAYMENT_PENALTY",
        "text": "Disputed invoices may be placed on hold without incurring late fees. Company must provide a 30-day cure notice before applying any penalty.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "PAYMENT_PENALTY",
        "text": "Late payment fee is a flat $25 per invoice, applied only after a 15-day grace period. Attorney's fee provisions are mutual and not one-sided.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # INDEMNIFICATION — exploitative
    {
        "category": "INDEMNIFICATION",
        "text": "Employee shall indemnify, defend, and hold harmless Company from any and all claims, damages, losses, or expenses, including attorney's fees, arising from Employee's acts or omissions, regardless of Company's contributory negligence.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "INDEMNIFICATION",
        "text": "User shall indemnify Company against any third-party claims arising from User's use of the service, whether or not Company has been negligent.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "INDEMNIFICATION",
        "text": "Each party shall indemnify the other for claims arising from its own gross negligence or willful misconduct.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    # INDEMNIFICATION — fair
    {
        "category": "INDEMNIFICATION",
        "text": "Indemnification obligations are mutual and proportional to each party's degree of fault. Neither party shall be required to indemnify the other for its own negligence.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "INDEMNIFICATION",
        "text": "User's indemnification obligation is limited to claims arising from User's material breach of this Agreement or intentional misconduct.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "INDEMNIFICATION",
        "text": "Indemnification does not apply to claims arising from Company's acts, omissions, negligence, or failure to comply with applicable laws.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },

    # JURISDICTION — exploitative
    {
        "category": "JURISDICTION",
        "text": "This Agreement shall be governed by the laws of the State of Delaware. Any legal proceedings must be filed exclusively in the state or federal courts of New Castle County, Delaware.",
        "risk_level": "MEDIUM",
        "is_user_favorable": False,
    },
    {
        "category": "JURISDICTION",
        "text": "All disputes shall be resolved under the laws of [Country], and the courts of [City] shall have exclusive jurisdiction. User waives any objection to such jurisdiction.",
        "risk_level": "HIGH",
        "is_user_favorable": False,
    },
    {
        "category": "JURISDICTION",
        "text": "This Agreement is governed by the laws of the state where User resides. Either party may bring suit in any court of competent jurisdiction.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    # JURISDICTION — fair
    {
        "category": "JURISDICTION",
        "text": "Jurisdiction for disputes shall be in the User's home country and applicable local laws shall govern consumer rights provisions.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "JURISDICTION",
        "text": "Each party may file in the jurisdiction most convenient to them. Forum selection shall not be used to create undue hardship for either party.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
    {
        "category": "JURISDICTION",
        "text": "Governing law is the jurisdiction of the User's principal place of business. Mandatory consumer protection laws of User's residence shall apply regardless.",
        "risk_level": "LOW",
        "is_user_favorable": True,
    },
]


async def main():
    """Seed the Firestore benchmark corpus with reference clauses."""
    from backend.utils.firestore_client import seed_benchmark_corpus
    count = await seed_benchmark_corpus(BENCHMARK_CLAUSES)
    print(f"Seeded {count} benchmark clauses successfully.")


if __name__ == "__main__":
    asyncio.run(main())
