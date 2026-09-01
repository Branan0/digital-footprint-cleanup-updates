#!/usr/bin/env python3
"""Build the supported UK, EU/EEA, US, and China jurisdiction targets."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKED_AT = "2026-09-01"
REVIEW_DUE = "2027-03-01"
GDPR_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
EDPB_MEMBERS_URL = "https://www.edpb.europa.eu/about-edpb/our-members_en"

COUNTRIES = {
    "AT": (
        "Austria",
        "de",
        "Österreichische Datenschutzbehörde",
        "https://www.dsb.gv.at/",
    ),
    "BE": (
        "Belgium",
        "fr",
        "Autorité de la protection des données",
        "https://www.autoriteprotectiondonnees.be/",
    ),
    "BG": (
        "Bulgaria",
        "bg",
        "Commission for Personal Data Protection",
        "https://www.cpdp.bg/",
    ),
    "HR": ("Croatia", "hr", "Agencija za zaštitu osobnih podataka", "https://azop.hr/"),
    "CY": (
        "Cyprus",
        "el",
        "Office of the Commissioner for Personal Data Protection",
        "https://www.gov.cy/dataprotection/",
    ),
    "CZ": (
        "Czechia",
        "cs",
        "Office for Personal Data Protection",
        "https://uoou.gov.cz/",
    ),
    "DK": ("Denmark", "da", "Datatilsynet", "https://www.datatilsynet.dk/"),
    "EE": ("Estonia", "et", "Andmekaitse Inspektsioon", "https://www.aki.ee/"),
    "FI": (
        "Finland",
        "fi",
        "Office of the Data Protection Ombudsman",
        "https://tietosuoja.fi/en/",
    ),
    "FR": (
        "France",
        "fr",
        "Commission nationale de l'informatique et des libertés",
        "https://www.cnil.fr/",
    ),
    "DE": (
        "Germany",
        "de",
        "Federal Commissioner for Data Protection and Freedom of Information",
        "https://www.bfdi.bund.de/EN/Home/home_node.html",
    ),
    "GR": ("Greece", "el", "Hellenic Data Protection Authority", "https://www.dpa.gr/"),
    "HU": (
        "Hungary",
        "hu",
        "National Authority for Data Protection and Freedom of Information",
        "https://www.naih.hu/",
    ),
    "IE": (
        "Ireland",
        "en",
        "Data Protection Commission",
        "https://www.dataprotection.ie/",
    ),
    "IT": (
        "Italy",
        "it",
        "Garante per la protezione dei dati personali",
        "https://www.garanteprivacy.it/",
    ),
    "LV": ("Latvia", "lv", "Data State Inspectorate", "https://www.dvi.gov.lv/lv"),
    "LT": (
        "Lithuania",
        "lt",
        "State Data Protection Inspectorate",
        "https://vdai.lrv.lt/",
    ),
    "LU": (
        "Luxembourg",
        "fr",
        "Commission nationale pour la protection des données",
        "https://cnpd.public.lu/en.html",
    ),
    "MT": (
        "Malta",
        "en",
        "Information and Data Protection Commissioner",
        "https://idpc.org.mt/",
    ),
    "NL": (
        "Netherlands",
        "nl",
        "Autoriteit Persoonsgegevens",
        "https://autoriteitpersoonsgegevens.nl/",
    ),
    "PL": ("Poland", "pl", "Personal Data Protection Office", "https://uodo.gov.pl/"),
    "PT": (
        "Portugal",
        "pt",
        "Comissão Nacional de Proteção de Dados",
        "https://www.cnpd.pt/",
    ),
    "RO": (
        "Romania",
        "ro",
        "National Supervisory Authority for Personal Data Processing",
        "https://www.dataprotection.ro/",
    ),
    "SK": (
        "Slovakia",
        "sk",
        "Office for Personal Data Protection",
        "https://dataprotection.gov.sk/uoou/",
    ),
    "SI": ("Slovenia", "sl", "Information Commissioner", "https://www.ip-rs.si/"),
    "ES": (
        "Spain",
        "es",
        "Agencia Española de Protección de Datos",
        "https://www.aepd.es/",
    ),
    "SE": (
        "Sweden",
        "sv",
        "Swedish Authority for Privacy Protection",
        "https://www.imy.se/",
    ),
    "IS": (
        "Iceland",
        "is",
        "Data Protection Authority",
        "https://island.is/en/o/the-data-protection-authority",
    ),
    "LI": (
        "Liechtenstein",
        "de",
        "Data Protection Authority",
        "https://www.datenschutzstelle.li/",
    ),
    "NO": ("Norway", "no", "Datatilsynet", "https://www.datatilsynet.no/"),
}


def source(title: str, url: str, authority_type: str, language: str) -> dict:
    return {
        "title": title,
        "url": url,
        "authority_type": authority_type,
        "language": language,
        "checked_at": CHECKED_AT,
    }


def gdpr_rights(basis: str = "GDPR") -> list[dict]:
    proof = [
        "Enough information to identify the account or record; extra identity evidence only where the controller has reasonable doubts about identity."
    ]
    return [
        {
            "right_id": "access",
            "title": "Access personal data",
            "legal_basis": f"{basis} Articles 12 and 15",
            "exceptions": [
                "Rights and freedoms of other people and applicable statutory restrictions may limit disclosure."
            ],
            "deadline_days": 30,
            "proof_requirements": proof,
        },
        {
            "right_id": "rectification",
            "title": "Correct inaccurate or incomplete personal data",
            "legal_basis": f"{basis} Article 16",
            "exceptions": [
                "The controller may verify the disputed facts before changing the record."
            ],
            "deadline_days": 30,
            "proof_requirements": proof,
        },
        {
            "right_id": "erasure",
            "title": "Erase personal data in specified circumstances",
            "legal_basis": f"{basis} Article 17",
            "exceptions": [
                "The right is not absolute.",
                "Freedom of expression, legal obligations, public tasks, public health, qualifying archives or research, and legal claims may justify retention.",
            ],
            "deadline_days": 30,
            "proof_requirements": proof,
        },
        {
            "right_id": "restriction",
            "title": "Restrict processing in specified circumstances",
            "legal_basis": f"{basis} Article 18",
            "exceptions": [
                "Restricted data may still be stored and used for consented purposes, legal claims, other people's rights, or important public interests."
            ],
            "deadline_days": 30,
            "proof_requirements": proof,
        },
        {
            "right_id": "portability",
            "title": "Receive and transmit qualifying data",
            "legal_basis": f"{basis} Article 20",
            "exceptions": [
                "This applies to qualifying automated processing based on consent or contract and must not harm other people's rights."
            ],
            "deadline_days": 30,
            "proof_requirements": proof,
        },
        {
            "right_id": "object",
            "title": "Object to specified processing",
            "legal_basis": f"{basis} Article 21",
            "exceptions": [
                "A controller may continue non-marketing processing where compelling legitimate grounds or legal claims override the objection."
            ],
            "deadline_days": 30,
            "proof_requirements": proof,
        },
    ]


def eea_pack(code: str) -> dict:
    country, language, authority, authority_url = COUNTRIES[code]
    return {
        "schema_version": 1,
        "iso_code": code,
        "country_name": country,
        "pack_version": 1,
        "language": language,
        "rights_state": "verified_rights",
        "rights": gdpr_rights(),
        "authoritative_sources": [
            source("General Data Protection Regulation", GDPR_URL, "statute", "en"),
            source(
                "European Data Protection Board member authorities",
                EDPB_MEMBERS_URL,
                "regulator",
                "en",
            ),
            source(authority, authority_url, "regulator", language),
        ],
        "routes": [
            {
                "route_id": "national-dpa-guidance-complaint",
                "title": f"{authority} guidance or complaint route",
                "url": authority_url,
                "language": language,
                "action_types": ["legal_request"],
                "route_basis": "legal",
                "minimum_disclosures": [
                    "name",
                    "contact_details",
                    "controller",
                    "record_locator",
                    "request_summary",
                ],
                "identity_document": "may_request",
                "automatic_submission_allowed": False,
            }
        ],
        "templates": [],
        "english_explanation": (
            "GDPR access, correction, erasure, restriction, portability and objection rights are available, subject to their legal conditions and exceptions. "
            "Send the initial request to the organisation controlling the data; use the national authority for guidance or escalation. "
            "The legal deadline is one calendar month, represented as 30 days for reminders, and may be extended by two further months for a complex request if the controller explains the extension. "
            "No request or identity document is submitted automatically."
        ),
        "effective_at": "2018-05-25",
        "reviewed_at": CHECKED_AT,
        "review_due_at": REVIEW_DUE,
    }


def uk_pack() -> dict:
    guidance = "https://ico.org.uk/for-the-public/your-right-to-get-your-data-deleted/"
    return {
        "schema_version": 1,
        "iso_code": "GB",
        "country_name": "United Kingdom",
        "pack_version": 1,
        "language": "en",
        "rights_state": "verified_rights",
        "rights": gdpr_rights("UK GDPR"),
        "authoritative_sources": [
            source(
                "UK data protection legislation and rights",
                "https://www.gov.uk/data-protection/the-data-protection-act",
                "government",
                "en",
            ),
            source(
                "ICO right to erasure guidance and request template",
                guidance,
                "regulator",
                "en",
            ),
            source(
                "Data Protection Act 2018",
                "https://www.legislation.gov.uk/ukpga/2018/12/contents",
                "statute",
                "en",
            ),
        ],
        "routes": [
            {
                "route_id": "ico-erasure-guidance",
                "title": "ICO erasure guidance and controller-request template",
                "url": guidance,
                "language": "en",
                "action_types": ["legal_request", "source_content_removal"],
                "route_basis": "legal",
                "minimum_disclosures": [
                    "name",
                    "contact_details",
                    "record_locator",
                    "request_summary",
                ],
                "identity_document": "may_request",
                "automatic_submission_allowed": False,
            }
        ],
        "templates": [
            {
                "template_id": "ico-erasure-request",
                "title": "ICO right-to-erasure request template",
                "language": "en",
                "official_url": guidance,
                "english_explanation": "The ICO page includes suggested wording for asking the organisation controlling the data to erase specified personal data.",
            }
        ],
        "english_explanation": (
            "The UK GDPR and Data Protection Act 2018 provide access, correction, erasure, restriction, portability and objection rights, subject to conditions and exemptions. "
            "The ICO says an erasure request can be verbal or written and the organisation normally has one calendar month to respond. "
            "The Data (Use and Access) Act has caused some ICO guidance to be reviewed, so the cited current ICO page takes precedence over generated wording. "
            "No request or identity document is submitted automatically."
        ),
        "effective_at": "2021-01-01",
        "reviewed_at": CHECKED_AT,
        "review_due_at": REVIEW_DUE,
    }


def china_pack() -> dict:
    law = "https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm"
    complaint = "https://www.pipchina.cn/h5/"
    return {
        "schema_version": 1,
        "iso_code": "CN",
        "country_name": "China",
        "pack_version": 1,
        "language": "zh",
        "rights_state": "verified_rights",
        "rights": [
            {
                "right_id": "access-copy",
                "title": "Consult and copy personal information",
                "legal_basis": "Personal Information Protection Law Articles 44 and 45",
                "exceptions": [
                    "The statutory exceptions referenced by Article 45 may apply."
                ],
                "deadline_days": None,
                "proof_requirements": [
                    "Enough information for the personal-information processor to identify the person and relevant record."
                ],
            },
            {
                "right_id": "correct-complete",
                "title": "Correct or complete inaccurate personal information",
                "legal_basis": "Personal Information Protection Law Article 46",
                "exceptions": [
                    "The processor may verify whether the information is inaccurate or incomplete."
                ],
                "deadline_days": None,
                "proof_requirements": [
                    "Identify the inaccurate or incomplete information and the requested correction."
                ],
            },
            {
                "right_id": "delete",
                "title": "Request deletion in specified circumstances",
                "legal_basis": "Personal Information Protection Law Article 47",
                "exceptions": [
                    "Where a statutory retention period has not expired or deletion is technically difficult, processing must be limited to storage and necessary security measures."
                ],
                "deadline_days": None,
                "proof_requirements": [
                    "Identify the processor, account or record and the Article 47 circumstance relied on."
                ],
            },
        ],
        "authoritative_sources": [
            source("Personal Information Protection Law", law, "statute", "zh"),
            source(
                "CAC personal-information complaint channel",
                complaint,
                "government",
                "zh",
            ),
        ],
        "routes": [
            {
                "route_id": "cac-personal-information-complaint",
                "title": "Personal-information unlawful-processing complaint channel",
                "url": complaint,
                "language": "zh",
                "action_types": ["legal_request"],
                "route_basis": "legal",
                "minimum_disclosures": [
                    "name",
                    "contact_details",
                    "processor",
                    "record_locator",
                    "request_summary",
                ],
                "identity_document": "may_request",
                "automatic_submission_allowed": False,
            }
        ],
        "templates": [],
        "english_explanation": (
            "China's Personal Information Protection Law gives individuals rights to consult, copy, correct, complete and, in the circumstances in Article 47, delete personal information. "
            "The law does not provide one universal response-day value for these requests, so provider-specific or later authoritative deadlines must be used. "
            "The linked CAC channel is a Chinese-language complaint route; it is always user-reviewed and never submitted automatically."
        ),
        "effective_at": "2021-11-01",
        "reviewed_at": CHECKED_AT,
        "review_due_at": REVIEW_DUE,
    }


def us_pack() -> dict:
    privacy_act = "https://www.usa.gov/government-files-privacy"
    return {
        "schema_version": 1,
        "iso_code": "US",
        "country_name": "United States",
        "pack_version": 1,
        "language": "en",
        "rights_state": "verified_rights",
        "rights": [
            {
                "right_id": "federal-privacy-act-access-correction",
                "title": "Access and correct covered federal-agency records",
                "legal_basis": "Privacy Act of 1974, 5 U.S.C. § 552a",
                "exceptions": [
                    "The right is limited to covered federal-agency systems of records and is subject to statutory exemptions."
                ],
                "deadline_days": None,
                "proof_requirements": [
                    "Contact the agency holding the record and provide the identity proof and record details that agency requires."
                ],
            }
        ],
        "authoritative_sources": [
            source(
                "USAGov Privacy Act request guidance", privacy_act, "government", "en"
            ),
            source(
                "FTC consumer guidance on company data sharing and state deletion rights",
                "https://consumer.ftc.gov/consumer-alerts/2024/04/when-companies-share-your-personal-information-without-your-permission",
                "government",
                "en",
            ),
        ],
        "routes": [
            {
                "route_id": "federal-agency-privacy-act-request",
                "title": "Privacy Act request to the federal agency holding the record",
                "url": privacy_act,
                "language": "en",
                "action_types": ["legal_request"],
                "route_basis": "legal",
                "minimum_disclosures": [
                    "name",
                    "contact_details",
                    "agency",
                    "record_locator",
                    "request_summary",
                ],
                "identity_document": "required",
                "automatic_submission_allowed": False,
            }
        ],
        "templates": [],
        "english_explanation": (
            "This country-level pack verifies the federal Privacy Act right to access and correct covered federal-agency records; it does not claim a nationwide general right to make every private company delete data. "
            "The FTC notes that some states provide company-data deletion rights, so a state-specific or sector-specific route must be selected before legal wording is generated for a private organisation. "
            "The federal route requires identity proof and is never submitted automatically."
        ),
        "effective_at": None,
        "reviewed_at": CHECKED_AT,
        "review_due_at": REVIEW_DUE,
    }


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def main() -> None:
    supported = json.loads(
        (ROOT / "schemas" / "supported-jurisdictions.json").read_text(encoding="utf-8")
    )
    packs = {code: eea_pack(code) for code in COUNTRIES}
    packs.update({"GB": uk_pack(), "CN": china_pack(), "US": us_pack()})
    if set(supported) != set(packs):
        raise RuntimeError("builder and supported-jurisdiction list disagree")
    targets = []
    for code in sorted(packs):
        content = (
            json.dumps(packs[code], ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        path = ROOT / "targets" / "jurisdictions" / f"{code}.json"
        write_atomic(path, content)
        targets.append(
            {
                "target_id": f"jurisdiction-{code.casefold()}",
                "target_type": "jurisdiction",
                "path": f"jurisdictions/{code}.json",
                "version": "1",
                "sequence": 1,
                "max_bytes": 65536,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    manifest = {
        "repository": "digital-footprint-cleanup-updates",
        "schema_version": 1,
        "targets": targets,
    }
    write_atomic(
        ROOT / "feed-manifest.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    print(json.dumps({"jurisdictions": len(packs), "targets": len(targets)}))


if __name__ == "__main__":
    main()
