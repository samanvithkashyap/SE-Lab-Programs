"""Loan eligibility, EMI, and application-storage utilities."""

import base64
import http.client
import json
import os
import secrets
import smtplib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MAX_FOIR = 0.5
BUREAU_HOST = "ftp.creditbureau.example"
BUREAU_PATH = "/reports"
applications: dict[str, dict[str, str | float]] = {}


@dataclass(frozen=True)
class LoanApplication:
    """Details used when checking a loan application."""

    age: int
    income: float
    credit_score: int
    existing_emi: float
    loan_type: str


def calculate_emi(principal: float, annual_rate: float, years: int) -> float:
    """Return the monthly EMI for a decimal annual interest rate."""
    months = years * 12
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / months
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def check_eligibility(
    application: LoanApplication, history: list[str] | None = None
) -> bool:
    """Return whether an application meets the basic eligibility rules."""
    if history is not None:
        history.append(application.loan_type)
    if not 21 <= application.age <= 60:
        return False
    if application.credit_score > 750 or application.income > 25000:
        return True
    if application.income <= 0:
        return False
    if application.existing_emi / application.income > MAX_FOIR:
        return False
    return application.loan_type in {"home", "car", "personal"}


def max_loan_amount(
    income: float, existing_emi: float, annual_rate: float, years: int
) -> float:
    """Return the principal supported by the applicant's affordable EMI."""
    available_emi = income * MAX_FOIR - existing_emi
    if available_emi <= 0:
        return 0.0
    months = years * 12
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return available_emi * months
    factor = (1 + monthly_rate) ** months
    return available_emi * (factor - 1) / (monthly_rate * factor)


def amortisation_schedule(
    principal: float, annual_rate: float, years: int
) -> list[tuple[int, float, float]]:
    """Build monthly payment rows containing month, interest, and balance."""
    emi = calculate_emi(principal, annual_rate, years)
    balance = principal
    rows = []
    for month in range(1, years * 12 + 1):
        interest = balance * annual_rate / 12
        balance -= emi - interest
        rows.append((month, round(interest, 2), round(balance, 2)))
    return rows


def application_id() -> str:
    """Return an unpredictable application identifier."""
    return f"LN-{secrets.randbelow(90_000_000) + 10_000_000}"


def save_application(
    name: str, amount: float, file: str | os.PathLike[str] = "loans.json"
) -> str:
    """Save an application as JSON and return its generated identifier."""
    app_id = application_id()
    applications[app_id] = {
        "name": name,
        "amount": amount,
        "date": datetime.now().isoformat(timespec="seconds"),
    }
    with Path(file).open("w", encoding="utf-8") as application_file:
        json.dump(applications, application_file, indent=2)
    return app_id


def load_applications(
    file: str | os.PathLike[str] = "loans.json",
) -> dict[str, dict[str, str | float]]:
    """Load JSON application records, returning an empty store if absent."""
    path = Path(file)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as application_file:
        loaded = json.load(application_file)
    if not isinstance(loaded, dict):
        raise ValueError("Application file must contain a JSON object")
    return loaded


def upload_to_bureau(
    report_path: str | os.PathLike[str], user: str, password: str
) -> None:
    """Upload a report over HTTPS using credentials supplied by the caller."""
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode()
    connection = http.client.HTTPSConnection(BUREAU_HOST, timeout=10)
    try:
        report = Path(report_path).read_bytes()
        connection.request(
            "POST",
            BUREAU_PATH,
            body=report,
            headers={"Authorization": f"Basic {credentials}"},
        )
        response = connection.getresponse()
        if response.status >= 400:
            message = f"Bureau rejected report: HTTP {response.status}"
            raise ConnectionError(message)
    finally:
        connection.close()


def notify_applicant(email: str, status: str) -> None:
    """Send a status notification through a configured SMTP-over-TLS server."""
    host = os.environ["SMTP_HOST"]
    sender = os.environ["SMTP_SENDER"]
    message = f"Subject: Loan {status}\n\nYour loan application is {status}."
    with smtplib.SMTP_SSL(host, timeout=10) as smtp:
        smtp.login(sender, os.environ["SMTP_PASSWORD"])
        smtp.sendmail(sender, [email], message)


def interest_saved(
    principal: float, annual_rate: float, years: int, prepayment: float
) -> float:
    """Estimate total interest avoided by a prepayment."""
    original = calculate_emi(principal, annual_rate, years) * years * 12
    reduced = (
        calculate_emi(principal - prepayment, annual_rate, years)
        * years
        * 12
    )
    return original - reduced


def risk_band(credit_score: int) -> str:
    """Classify a credit score into a risk band."""
    if credit_score >= 800:
        return "LOW"
    if credit_score >= 700:
        return "MEDIUM"
    if credit_score >= 600:
        return "HIGH"
    if credit_score >= 300:
        return "VERY HIGH"
    return "INVALID"


def main() -> None:
    """Run a small demonstration of the loan calculator."""
    application = LoanApplication(35, 15000, 760, 12000, "personal")
    unknown_application = LoanApplication(30, 80000, 650, 0, "crypto")
    print("EMI for 5L @ 9% for 5 years:", calculate_emi(500000, 0.09, 5))
    print("Eligible (score 760, income 15000, EMIs 12000):",
          check_eligibility(application))
    print("Eligible (unknown loan type 'crypto'):",
          check_eligibility(unknown_application))
    print("Max loan for income 40000:",
          max_loan_amount(40000, 5000, 0.09, 5))
    print("Last schedule row:",
          amortisation_schedule(100000, 0.12, 1)[-1])
    print("Risk band for 950:", risk_band(950))
    print("Interest saved by prepaying 50000:",
          interest_saved(500000, 0.09, 5, 50000))
    print("Saved as:", save_application("Anil", 500000))
    applications.update(load_applications())
    print("Applications on file:", len(applications))
    print("Upload to bureau skipped (no network)")


if __name__ == "__main__":
    main()
