"""
lab/generate_docs.py

Generates all 17 knowledge base PDF documents for the FreeStyle Libre
AI Support Lab. Run this before deploying knowledge bases.

Usage:
    pip install fpdf2
    python3 lab/generate_docs.py
"""

import os
from fpdf import FPDF


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_bases", "docs")

DOCUMENTS = {
    "freestyle-libre-general-faq.pdf": {
        "title": "FreeStyle Libre - General FAQ",
        "content": [
            ("How long does a FreeStyle Libre sensor last?",
             "FreeStyle Libre 2 and 3 sensors are approved for up to 14 days of continuous wear. After 14 days the sensor expires and must be replaced with a new one."),
            ("Where do I apply the sensor?",
             "Apply the sensor to the back of your upper arm only. Avoid bony areas, areas with scars, or areas where clothing may rub against the sensor."),
            ("How do I scan my sensor?",
             "Hold your reader or compatible smartphone near and over the sensor. The scan takes less than 1 second. You will hear a beep or feel a vibration when the scan is successful."),
            ("What is the warm-up period?",
             "After applying a new sensor, there is a 60-minute warm-up period before the sensor begins providing glucose readings. During this time the sensor is initializing."),
            ("Can I scan through clothing?",
             "You can scan through up to 4mm of clothing. However, direct skin contact is recommended for the most reliable scan."),
            ("Is the FreeStyle Libre sensor waterproof?",
             "The sensor is water resistant up to 1 metre for 30 minutes (IP27 rated). You can shower, swim, and exercise while wearing it. However, prolonged water exposure may affect adhesion."),
            ("How accurate is the FreeStyle Libre sensor?",
             "FreeStyle Libre uses factory calibration and has been clinically validated. The sensor measures interstitial glucose which may lag behind blood glucose by up to 15 minutes during rapid changes."),
            ("What do I do if my sensor stops working?",
             "If your sensor displays an error message or stops providing readings, contact FreeStyle Libre Support. You may be eligible for a replacement if the sensor failed within its approved wear period."),
        ]
    },
    "freestyle-libre-sensor-application-faq.pdf": {
        "title": "FreeStyle Libre - Sensor Application FAQ",
        "content": [
            ("How do I prepare my skin before applying?",
             "Clean the application site with an alcohol wipe and allow it to dry completely before applying the sensor. Do not apply lotions, creams, sunscreen, or oils to the site."),
            ("Can I reapply a sensor that has fallen off?",
             "No. Once a sensor has been removed from the skin it cannot be reapplied. You will need a new sensor."),
            ("How do I apply the sensor correctly?",
             "Press the applicator firmly against the back of the upper arm until you hear a click. Hold for 5 seconds before removing the applicator. Press gently around the edges to ensure adhesion."),
            ("What if the sensor falls off early?",
             "If your sensor falls off before the 14-day wear period ends, contact FreeStyle Libre Support. You may be eligible for a replacement depending on when it fell off and the circumstances."),
            ("Can I use an overpatch?",
             "Yes. Overpatches are available to help keep the sensor in place during physical activities or swimming. Contact your healthcare provider or pharmacy for availability."),
        ]
    },
    "freestyle-libre-app-connectivity-faq.pdf": {
        "title": "FreeStyle Libre - App Connectivity FAQ",
        "content": [
            ("Which smartphones are compatible with FreeStyle LibreLink?",
             "A full list of compatible devices is available at freestyle.abbott. Generally, iPhones with iOS 15 or later and Android phones with Android 9 or later with NFC are supported."),
            ("Why won't my app scan the sensor?",
             "Ensure NFC is enabled on your phone. Remove any thick or metal-backed phone case. Hold the phone flat and centered directly over the sensor. Try toggling NFC off and back on."),
            ("Do I need internet access to scan?",
             "No. Scanning works without internet. However, an internet connection is required to sync your data to LibreView and to receive software updates."),
            ("How do I set up the FreeStyle LibreLink app?",
             "Download FreeStyle LibreLink from the App Store or Google Play for your region. Create or log into your LibreView account, then scan your sensor to begin."),
            ("What do I do if the app shows an error after scanning?",
             "Force-close and reopen the app. If the error persists, try clearing the app cache (Android) or offloading and reinstalling the app (iOS). Contact support if the issue continues."),
        ]
    },
    "sensor-error-codes-guide.pdf": {
        "title": "FreeStyle Libre - Sensor Error Codes Guide",
        "content": [
            ("E-1: Sensor Warming Up",
             "The sensor is in its 60-minute initialization period. Wait for the warm-up to complete before expecting glucose readings. This is normal and not a sensor failure."),
            ("E-2: Sensor Communication Error",
             "The reader or app could not communicate with the sensor. Try scanning again by holding the device flat over the sensor for 1-2 seconds. If this persists, try in a different location away from electromagnetic interference."),
            ("E-3: Sensor Failed",
             "The sensor has experienced a failure and cannot provide readings. This is a confirmed device malfunction. Contact FreeStyle Libre Support for a replacement. You may be eligible under the warranty policy."),
            ("E-4: Sensor Expired",
             "The sensor has reached the end of its 14-day approved wear period. Replace with a new sensor."),
            ("ERR: General Error",
             "A general communication or processing error occurred. Re-scan the sensor. If the error persists after 3 attempts, contact support."),
            ("-- (Dashes): Reading Not Available",
             "The sensor cannot provide a reading at this time. This may occur immediately after application (warm-up), during rapid glucose changes, or if the sensor is failing. Try scanning again in 10 minutes."),
        ]
    },
    "sensor-adhesion-troubleshooting.pdf": {
        "title": "FreeStyle Libre - Sensor Adhesion Troubleshooting",
        "content": [
            ("Why did my sensor fall off early?",
             "Common causes include: skin not fully dry at application, presence of lotion, oil, or sunscreen, excessive sweating, prolonged water immersion, or application to a high-movement area."),
            ("How can I improve adhesion?",
             "Apply to clean dry skin. Use an alcohol wipe and let it dry for 30 seconds before applying. Avoid bony prominences. Consider an overpatch for active lifestyles or swimming."),
            ("Does swimming affect the sensor?",
             "The sensor is water resistant for 30 minutes at 1 metre depth. Prolonged swimming or hot water exposure can loosen the adhesive. An overpatch is recommended for regular swimmers."),
            ("What should I do if the edges are lifting?",
             "Gently press the edges back down. Do not apply adhesive products directly to the sensor electronics. If significant separation has occurred, the sensor may need to be replaced."),
            ("Can I use skin tape to hold the sensor?",
             "Yes, medical-grade skin tape around the edges of the sensor (not over the scanning window) can help maintain adhesion. Do not tape over the top of the sensor dome."),
        ]
    },
    "reader-device-troubleshooting.pdf": {
        "title": "FreeStyle Libre - Reader Device Troubleshooting",
        "content": [
            ("Reader will not turn on",
             "Connect the reader to the supplied USB charging cable. Allow to charge for at least 30 minutes. If still unresponsive, hold the power button for 10 seconds to perform a hard reset."),
            ("Reader not scanning sensor",
             "Hold the reader flat over the center of the sensor for 1-2 full seconds. Remove any case if using one. Ensure no metal objects are between the reader and sensor."),
            ("Reader screen is blank or frozen",
             "Hold the power button for 10 seconds to restart the device. If the screen remains blank after a restart, the device may require replacement."),
            ("Reader not charging",
             "Check the USB cable and charging port for debris. Try a different USB power source. If the charging indicator does not appear after 30 minutes, contact support."),
            ("How do I update reader software?",
             "Connect the reader to a PC or Mac with the FreeStyle LibreLink software installed. The software will check for and install available updates automatically."),
        ]
    },
    "mobile-app-troubleshooting.pdf": {
        "title": "FreeStyle Libre - Mobile App Troubleshooting",
        "content": [
            ("App crashes or freezes",
             "Force-close the app and reopen. Ensure you have the latest version installed. On Android, clear the app cache via Settings > Apps > FreeStyle LibreLink > Storage > Clear Cache."),
            ("App not syncing to LibreView",
             "Ensure your phone has an active internet connection. Log out and log back into LibreView within the app. Check that data sync is enabled in app settings."),
            ("Notifications not working",
             "Check that notifications are enabled for FreeStyle LibreLink in your phone's notification settings. Ensure Do Not Disturb mode is not blocking alerts."),
            ("Lost historical data",
             "Data is backed up to LibreView when connected to internet. Log into LibreView.com to view historical data. Note: the app stores 90 days of data locally."),
            ("App shows wrong time or date",
             "Ensure your phone's date and time are set to automatic. The app uses your phone's system clock for timestamps."),
        ]
    },
    "freestyle-libre-warranty-policy-2024.pdf": {
        "title": "FreeStyle Libre Warranty Policy 2024",
        "content": [
            ("Section 1.1 - Approved Wear Duration",
             "FreeStyle Libre 2 and FreeStyle Libre 3 sensors are warranted for the approved 14-day wear period. Sensor failures reported after the 14-day wear window are not covered under this warranty."),
            ("Section 2.4 - Device Malfunction",
             "Sensors that display a recognized error code (E-1 through E-9, ERR) and fail to provide readings within the approved wear period qualify for replacement under this warranty."),
            ("Section 3.1 - Premature Detachment",
             "Sensors that detach from the skin before the end of the approved wear period, where detachment is not caused by user action, qualify for replacement review."),
            ("Section 5.1 - Warranty Coverage",
             "This warranty covers manufacturing defects, premature sensor failure, and device malfunctions under normal use conditions during the approved wear period."),
            ("Section 5.2 - Exclusions",
             "This warranty does not cover: damage caused by user (impact, crushing, puncture), exposure to temperatures outside 4-40 degrees C, use beyond the approved wear period, or sensors not purchased from an authorized distributor."),
        ]
    },
    "sensor-warranty-exclusions.pdf": {
        "title": "FreeStyle Libre - Warranty Exclusions Detail",
        "content": [
            ("User-caused physical damage",
             "Damage resulting from dropping, crushing, or puncturing the sensor is excluded from warranty coverage. This includes damage caused by tight clothing or equipment."),
            ("Temperature exposure",
             "Sensors exposed to temperatures below 4 degrees C or above 40 degrees C during wear or storage may fail. Such failures are excluded from warranty coverage."),
            ("Unauthorized modification",
             "Any modification to the sensor, applicator, or reader voids the warranty. This includes attempting to reuse a single-use sensor."),
            ("Counterfeit products",
             "Products not purchased from an authorized Abbott distributor or pharmacy are not covered under Abbott's warranty policy."),
        ]
    },
    "sensor-replacement-policy-2024.pdf": {
        "title": "FreeStyle Libre Sensor Replacement Policy 2024",
        "content": [
            ("Section 3.1 - Premature Detachment",
             "Sensors that fall off before Day 12 of the wear period, where no user-caused damage is identified, are eligible for replacement. The customer must provide the lot number and sensor serial number."),
            ("Section 4.2 - Accuracy Complaints",
             "Reports of inaccurate readings within the approved wear window, where no error code is displayed and no physical damage is present, are subject to specialist review before a replacement determination is made."),
            ("Section 4.3 - Accuracy with Damage",
             "Inaccuracy claims where physical damage is also present require specialist review to determine whether the damage contributed to the inaccuracy."),
            ("Section 5.0 - Replacement Process",
             "Approved replacements are shipped within 3-5 business days to the address on file. Customers must return the failed sensor packaging including the lot number label."),
            ("Section 6.0 - Manual Review",
             "Cases that do not clearly match the standard eligibility criteria are referred to the specialist review queue. A specialist will contact the customer within 1-2 business days."),
        ]
    },
    "replacement-eligibility-matrix.pdf": {
        "title": "FreeStyle Libre - Replacement Eligibility Matrix",
        "content": [
            ("Eligible - Premature Detachment",
             "Condition: Sensor fell off before Day 12. No user-caused damage reported. Action: Approve replacement. Policy: Section 3.1"),
            ("Eligible - Confirmed Sensor Failure",
             "Condition: Recognized error code displayed (E-3, ERR, etc.) within 14-day wear period. Action: Approve replacement. Policy: Section 2.4"),
            ("Needs Review - Inaccurate Readings",
             "Condition: Inaccuracy reported within wear window. No error code. No damage. Action: Refer to specialist. Policy: Section 4.2"),
            ("Needs Review - Inaccuracy with Damage",
             "Condition: Inaccuracy reported AND physical damage present. Action: Refer to specialist. Policy: Section 4.3"),
            ("Not Eligible - Post Wear Period",
             "Condition: Issue reported after Day 14 or sensor used beyond approved duration. Action: Deny replacement. Policy: Section 1.1"),
            ("Not Eligible - User Damage",
             "Condition: Physical damage caused by user impact, crushing, or puncture. Action: Deny replacement. Policy: Section 5.2"),
        ]
    },
    "proof-of-purchase-requirements.pdf": {
        "title": "FreeStyle Libre - Proof of Purchase Requirements",
        "content": [
            ("Required Information",
             "All replacement requests require: (1) Lot number from the sensor packaging label, (2) Sensor serial number from the applicator packaging. These identify the specific product batch."),
            ("Where to find the Lot Number",
             "The lot number is printed on the white label on the sensor packaging box and on the applicator pouch. It begins with letters followed by numbers (e.g., XY-990011)."),
            ("Where to find the Serial Number",
             "The sensor serial number is printed on the applicator packaging pouch. It is 8-16 alphanumeric characters (e.g., AB12345678)."),
            ("Optional Supporting Information",
             "While not required, the following may help expedite your claim: date of purchase, pharmacy name, prescription date, or photos of the failed sensor and packaging."),
        ]
    },
    "support-agent-handbook.pdf": {
        "title": "FreeStyle Libre Support Agent Handbook",
        "content": [
            ("Agent Role and Boundaries",
             "The AI support agent handles device troubleshooting, eligibility assessment, case intake, and case creation. It does not provide medical advice, diagnoses, or treatment recommendations."),
            ("Escalation Triggers",
             "Always escalate to a human agent when: customer requests a human, potential health risk is described, troubleshooting is exhausted, customer is dissatisfied, or case complexity is high."),
            ("HIPAA Compliance",
             "Never log or store PII in plain text. Mask all personal data in logs. Do not collect SSN, insurance information, or glucose values. Refer health questions to healthcare providers."),
            ("Communication Guidelines",
             "Be warm, calm, and professional. Use plain language. Acknowledge frustration. Never provide medical interpretations. Always confirm case details before submission."),
            ("Case Submission Checklist",
             "Before submitting: verify all 12 required fields are collected, confirm eligibility status, review case summary with customer, obtain explicit confirmation before submitting."),
        ]
    },
    "escalation-procedures.pdf": {
        "title": "FreeStyle Libre - Escalation Procedures",
        "content": [
            ("When to Escalate Immediately",
             "Escalate without delay when: customer requests human agent, customer describes symptoms or health risk, customer mentions a medical emergency, or case involves a potential adverse event."),
            ("Escalation Information to Transfer",
             "When escalating, pass: full conversation summary, escalation trigger reason, customer contact preference, case number if created, all collected information (PII masked)."),
            ("Tier 2 Routing",
             "Standard escalations route to the Tier 2 Support queue. Health risk cases are marked PRIORITY: HEALTH RISK and route to the senior support team."),
            ("Adverse Event Reporting",
             "If a customer describes a potential adverse event (device malfunction affecting health management), the case must be forwarded to the Abbott pharmacovigilance team per regulatory requirements."),
            ("Follow-Up SLA",
             "Tier 2 agents respond to escalated cases within 2 business hours. Health risk priority cases are responded to within 30 minutes during business hours."),
        ]
    },
    "product-catalogue-freestyle-libre.pdf": {
        "title": "FreeStyle Libre - Product Catalogue",
        "content": [
            ("FreeStyle Libre 3",
             "The smallest, thinnest CGM sensor available. 14-day wear. Real-time glucose readings every minute sent directly to the LibreLink app. Compatible with iOS and Android. No fingerstick calibration required."),
            ("FreeStyle Libre 2",
             "14-day wear sensor with optional glucose alarms. Alerts when glucose is too high or too low. Compatible with the FreeStyle LibreLink app and the FreeStyle Libre 2 reader device."),
            ("FreeStyle Libre 14 Day",
             "The original FreeStyle Libre sensor with a 14-day wear period. Requires a compatible reader device or smartphone to scan. No real-time streaming."),
            ("FreeStyle Libre Reader",
             "Dedicated reader device for scanning FreeStyle Libre sensors. Stores up to 90 days of glucose data. Does not require a smartphone. Charges via USB."),
        ]
    },
    "regulatory-compliance-notes.pdf": {
        "title": "FreeStyle Libre - Regulatory Compliance Notes",
        "content": [
            ("FDA Classification",
             "FreeStyle Libre is a Class II medical device regulated by the FDA under 21 CFR Part 862. It is intended for use in people with diabetes aged 4 years and older."),
            ("AI Support System Classification",
             "The AI support system is a device support and logistics tool only. It does not constitute a Software as a Medical Device (SaMD) and must not be used for clinical decision support."),
            ("Adverse Event Reporting",
             "Device malfunctions that may have caused or contributed to a serious injury must be reported to Abbott's pharmacovigilance team and may require MDR reporting to the FDA under 21 CFR Part 803."),
            ("HIPAA Compliance",
             "All customer support interactions involving personal health information must be handled in accordance with HIPAA requirements. A Business Associate Agreement (BAA) must be in place with all technology vendors."),
            ("Data Retention",
             "Support case records and interaction logs must be retained for a minimum of 7 years per FDA requirements for medical device manufacturers."),
        ]
    },
    "customer-communication-templates.pdf": {
        "title": "FreeStyle Libre - Customer Communication Templates",
        "content": [
            ("Replacement Approved",
             "Your FreeStyle Libre sensor has been approved for replacement. A new sensor will be shipped to your address on file within 3-5 business days. Your case number is [CASE_ID]. Please keep this for your records."),
            ("Needs Specialist Review",
             "Thank you for contacting FreeStyle Libre Support. Your case has been referred to our specialist team for review. A support specialist will contact you within 1-2 business days. Your case number is [CASE_ID]."),
            ("Not Eligible",
             "We have reviewed your request and determined that your sensor does not qualify for replacement under our current warranty policy. For further assistance, please contact your healthcare provider or visit freestyle.abbott."),
            ("Human Escalation",
             "I understand your concern and want to make sure you get the best possible support. I am connecting you with a member of our specialized support team right now. Please hold while I transfer your case."),
            ("Case Created Confirmation",
             "Your support case has been successfully created. Your case number is [CASE_ID]. You will receive a confirmation email at [EMAIL] within 24 hours. You can check your case status at any time by returning to this chat."),
        ]
    },
}


def create_pdf(filename: str, title: str, content: list) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_fill_color(0, 87, 168)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, title, ln=True, fill=True, align="C")
    pdf.ln(4)

    # Content
    for question, answer in content:
        # Question / heading
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(0, 87, 168)
        pdf.multi_cell(0, 7, question)

        # Answer
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 6, answer)
        pdf.ln(4)

    # Footer
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Abbott Diabetes Care - FreeStyle Libre Support Knowledge Base - For internal use only", align="C")

    output_path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(output_path)
    print(f"  Created: {filename}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\n" + "=" * 55)
    print("  FreeStyle Libre Lab - Knowledge Base PDF Generator")
    print("=" * 55)
    print(f"\n  Output directory: {OUTPUT_DIR}")
    print(f"  Generating {len(DOCUMENTS)} documents...\n")

    success = 0
    for filename, doc in DOCUMENTS.items():
        try:
            create_pdf(filename, doc["title"], doc["content"])
            success += 1
        except Exception as e:
            print(f"  ERROR generating {filename}: {e}")

    print(f"\n  {success}/{len(DOCUMENTS)} documents created successfully.")
    print("\n  Next step:")
    print("  Run 'make deploy' to import knowledge bases with these documents.")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
