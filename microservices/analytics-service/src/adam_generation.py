"""
ADaM (Analysis Data Model) Dataset Generation Module

Generates CDISC ADaM-compliant analysis datasets:
- ADSL: Subject-Level Analysis Dataset
- ADTTE: Time-to-Event Analysis Dataset
- ADAE: Adverse Event Analysis Dataset
- BDS: Basic Data Structure for labs/vitals

Author: Analytics Service
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_adsl(
    demographics_data: List[Dict[str, Any]],
    vitals_data: Optional[List[Dict[str, Any]]] = None,
    ae_data: Optional[List[Dict[str, Any]]] = None,
    study_id: str = "STUDY001",
    study_start_date: str = "2025-01-01"
) -> List[Dict[str, Any]]:
    """
    Generate ADSL (Subject-Level Analysis Dataset).

    ADSL is the cornerstone ADaM dataset containing one record per subject
    with key demographic, treatment, and disposition variables.

    Args:
        demographics_data: List of subject demographics
        vitals_data: Optional vitals data for baseline values
        ae_data: Optional AE data for safety flags
        study_id: Study identifier
        study_start_date: Study start date (YYYY-MM-DD)

    Returns:
        List of ADSL records
    """
    adsl_records = []

    # Convert vitals and AE to DataFrames for easier lookup
    vitals_df = pd.DataFrame(vitals_data) if vitals_data else None
    ae_df = pd.DataFrame(ae_data) if ae_data else None

    study_start = datetime.strptime(study_start_date, "%Y-%m-%d")

    for idx, subject in enumerate(demographics_data, 1):
        subject_id = subject.get("SubjectID")
        treatment_arm = subject.get("TreatmentArm", "Placebo")

        # Generate random dates
        screening_date = study_start + timedelta(days=np.random.randint(1, 180))
        randomization_date = screening_date + timedelta(days=np.random.randint(7, 30))
        treatment_start_date = randomization_date + timedelta(days=1)

        # Determine disposition
        completed = np.random.random() > 0.15  # 85% completion rate
        if completed:
            treatment_end_date = treatment_start_date + timedelta(days=np.random.randint(300, 400))
            disposition = "COMPLETED"
            disposition_reason = None
        else:
            treatment_end_date = treatment_start_date + timedelta(days=np.random.randint(30, 300))
            disposition = "DISCONTINUED"
            disposition_reason = np.random.choice([
                "ADVERSE EVENT",
                "LACK OF EFFICACY",
                "WITHDRAWAL BY SUBJECT",
                "LOST TO FOLLOW-UP",
                "PROTOCOL DEVIATION"
            ])

        # Baseline vitals (if available)
        if vitals_df is not None and len(vitals_df) > 0:
            subject_vitals = vitals_df[
                (vitals_df["SubjectID"] == subject_id) &
                (vitals_df["VisitName"].isin(["Screening", "Baseline"]))
            ]
            if not subject_vitals.empty:
                baseline_sbp = subject_vitals["SystolicBP"].iloc[0] if "SystolicBP" in subject_vitals.columns else None
                baseline_dbp = subject_vitals["DiastolicBP"].iloc[0] if "DiastolicBP" in subject_vitals.columns else None
            else:
                baseline_sbp = None
                baseline_dbp = None
        else:
            baseline_sbp = None
            baseline_dbp = None

        # Safety flags
        if ae_df is not None and len(ae_df) > 0:
            subject_aes = ae_df[ae_df["SubjectID"] == subject_id]
            has_any_ae = len(subject_aes) > 0
            has_serious_ae = len(subject_aes[subject_aes["Serious"] == "Yes"]) > 0 if has_any_ae else False
            has_related_ae = len(subject_aes[subject_aes["Relationship"].str.contains("Related", na=False)]) > 0 if has_any_ae else False
        else:
            has_any_ae = False
            has_serious_ae = False
            has_related_ae = False

        # Calculate treatment duration
        treatment_duration = (treatment_end_date - treatment_start_date).days

        # ADSL record
        adsl_record = {
            # Study Identifiers
            "STUDYID": study_id,
            "USUBJID": f"{study_id}-{subject_id}",
            "SUBJID": subject_id,

            # Demographics
            "AGE": subject.get("Age"),
            "AGEU": "YEARS",
            "AGEGR1": categorize_age(subject.get("Age")),
            "SEX": subject.get("Gender", "Male")[0],  # M/F
            "RACE": subject.get("Race", "White").upper(),
            "ETHNIC": "NOT HISPANIC OR LATINO" if subject.get("Ethnicity") == "Not Hispanic" else "HISPANIC OR LATINO",

            # Physical Characteristics
            "HEIGHTBL": subject.get("Height"),  # cm
            "WEIGHTBL": subject.get("Weight"),  # kg
            "BMIBL": subject.get("BMI"),

            # Treatment
            "ARM": treatment_arm,
            "TRT01P": treatment_arm,  # Planned treatment
            "TRT01A": treatment_arm,  # Actual treatment
            "TRT01PN": 1 if treatment_arm == "Active" else 2,  # Numeric
            "TRT01AN": 1 if treatment_arm == "Active" else 2,

            # Important Dates (ISO 8601 format)
            "RFSTDTC": screening_date.strftime("%Y-%m-%d"),  # Reference start date
            "RFENDTC": treatment_end_date.strftime("%Y-%m-%d"),  # Reference end date
            "RFXSTDTC": treatment_start_date.strftime("%Y-%m-%d"),  # Treatment start
            "RFXENDTC": treatment_end_date.strftime("%Y-%m-%d"),  # Treatment end
            "RFICDTC": randomization_date.strftime("%Y-%m-%d"),  # Informed consent

            # Study Day Variables
            "TRTSDT": 1,  # Treatment start day
            "TRTEDT": treatment_duration,  # Treatment end day

            # Disposition
            "ITTFL": "Y",  # Intent-to-treat flag
            "SAFFL": "Y" if treatment_duration >= 1 else "N",  # Safety population
            "FASFL": "Y" if treatment_duration >= 1 else "N",  # Full analysis set
            "COMPLFL": "Y" if completed else "N",  # Completed study
            "DCSREAS": disposition_reason,  # Discontinuation reason
            "DTHFL": "N",  # Death flag (would be Y if died)

            # Baseline Values
            "BSBPBL": baseline_sbp,  # Baseline systolic BP
            "BDBPBL": baseline_dbp,  # Baseline diastolic BP

            # Safety Flags
            "AOCCFL": "Y" if has_any_ae else "N",  # Any AE occurred
            "ASAEFL": "Y" if has_serious_ae else "N",  # Any SAE occurred
            "ARELFL": "Y" if has_related_ae else "N",  # Any related AE occurred

            # Analysis Populations
            "PPROTFL": "Y" if completed and treatment_duration >= 84 else "N",  # Per-protocol
            "RANDFL": "Y",  # Randomized flag

            # Site and Country
            "SITEID": f"Site{(idx % 5) + 1:03d}",
            "COUNTRY": "USA"
        }

        adsl_records.append(adsl_record)

    return adsl_records


def categorize_age(age: int) -> str:
    """Categorize age into standard age groups."""
    if age < 18:
        return "<18"
    elif age < 65:
        return "18-64"
    elif age < 75:
        return "65-74"
    else:
        return ">=75"


def generate_adtte(
    survival_data: List[Dict[str, Any]],
    adsl_data: List[Dict[str, Any]],
    study_id: str = "STUDY001"
) -> List[Dict[str, Any]]:
    """
    Generate ADTTE (Time-to-Event Analysis Dataset).

    ADTTE contains time-to-event data for survival analysis endpoints.

    Args:
        survival_data: List of survival/TTE records
        adsl_data: ADSL data for subject-level info
        study_id: Study identifier

    Returns:
        List of ADTTE records
    """
    adtte_records = []

    # Convert ADSL to dict for quick lookup
    adsl_dict = {rec["SUBJID"]: rec for rec in adsl_data}

    for idx, tte_record in enumerate(survival_data, 1):
        subject_id = tte_record["SubjectID"]
        adsl_rec = adsl_dict.get(subject_id, {})

        # Multiple parameterizations of time-to-event
        event_occurred = tte_record["EventOccurred"]
        event_time_months = tte_record["EventTime"]
        event_time_days = event_time_months * 30  # Convert to days

        # Create ADTTE record
        adtte_record = {
            # Identifiers
            "STUDYID": study_id,
            "USUBJID": f"{study_id}-{subject_id}",
            "SUBJID": subject_id,

            # Parameter
            "PARAMCD": "OS",  # Overall Survival
            "PARAM": "Overall Survival",
            "PARCAT1": "EFFICACY",

            # Treatment
            "TRTP": adsl_rec.get("TRT01P"),
            "TRTPN": adsl_rec.get("TRT01PN"),

            # Analysis Value (time in days)
            "AVAL": round(event_time_days, 1),
            "AVALC": str(round(event_time_days, 1)),
            "ADY": int(event_time_days),  # Analysis day

            # Event Flag
            "CNSR": 1 if tte_record["Censored"] else 0,  # 1=censored, 0=event
            "EVNTDESC": tte_record["EventType"],

            # Baseline and Change
            "BASE": None,  # Not applicable for TTE
            "CHG": None,

            # Analysis Flags
            "ANL01FL": "Y",  # Analysis flag 1
            "ITTFL": adsl_rec.get("ITTFL"),
            "SAFFL": adsl_rec.get("SAFFL"),

            # Stratification Variables
            "AGEGR1": adsl_rec.get("AGEGR1"),
            "SEX": adsl_rec.get("SEX"),

            # Site
            "SITEID": adsl_rec.get("SITEID")
        }

        adtte_records.append(adtte_record)

    return adtte_records


def generate_adae(
    ae_data: List[Dict[str, Any]],
    adsl_data: List[Dict[str, Any]],
    study_id: str = "STUDY001"
) -> List[Dict[str, Any]]:
    """
    Generate ADAE (Adverse Event Analysis Dataset).

    ADAE contains analysis-ready adverse event data.

    Args:
        ae_data: List of adverse event records
        adsl_data: ADSL data for subject-level info
        study_id: Study identifier

    Returns:
        List of ADAE records
    """
    adae_records = []

    # Convert ADSL to dict for quick lookup
    adsl_dict = {rec["SUBJID"]: rec for rec in adsl_data}

    for idx, ae in enumerate(ae_data, 1):
        subject_id = ae["SubjectID"]
        adsl_rec = adsl_dict.get(subject_id, {})

        # Determine severity grade
        severity = ae.get("Severity", "Mild")
        if severity == "Mild":
            aetoxgr = "1"
        elif severity == "Moderate":
            aetoxgr = "2"
        elif severity == "Severe":
            aetoxgr = "3"
        else:
            aetoxgr = "1"

        # Seriousness
        serious = ae.get("Serious", "No")
        aeser = "Y" if serious == "Yes" else "N"

        # Relationship
        relationship = ae.get("Relationship", "Not Related")
        aerel = "RELATED" if "Related" in relationship else "NOT RELATED"

        # Treatment-emergent flag (would need treatment start date from ADSL)
        trtemfl = "Y"  # Assume all are treatment-emergent for this example

        # Create ADAE record
        adae_record = {
            # Identifiers
            "STUDYID": study_id,
            "USUBJID": f"{study_id}-{subject_id}",
            "SUBJID": subject_id,
            "AESEQ": idx,

            # AE Description
            "AEDECOD": ae["PT"],  # Preferred term
            "AEBODSYS": ae["SOC"],  # System organ class
            "AELLT": ae["PT"],  # Lower level term (same as PT for simplicity)
            "AEHLT": ae["SOC"],  # High level term

            # Treatment
            "TRTP": adsl_rec.get("TRT01P"),
            "TRTPN": adsl_rec.get("TRT01PN"),
            "TRTA": adsl_rec.get("TRT01A"),
            "TRTAN": adsl_rec.get("TRT01AN"),

            # Severity and Relationship
            "AESEV": severity.upper(),
            "AETOXGR": aetoxgr,
            "AESER": aeser,
            "AEREL": aerel,

            # Dates
            "ASTDT": ae.get("OnsetDate"),
            "AENDT": None,  # End date (not provided in sample data)
            "ASTDY": None,  # Study day of start
            "AENDY": None,  # Study day of end

            # Flags
            "TRTEMFL": trtemfl,  # Treatment-emergent
            "AOCCFL": "Y",  # AE occurrence flag
            "AOCCSFL": "Y" if aeser == "Y" else "N",  # Serious AE occurrence
            "AOCC01FL": "Y",  # First occurrence

            # Analysis Flags
            "ANL01FL": "Y",
            "ITTFL": adsl_rec.get("ITTFL"),
            "SAFFL": adsl_rec.get("SAFFL"),

            # Outcome
            "AEOUT": "RECOVERED" if serious == "No" else "RECOVERING",

            # Action Taken
            "AEACN": "DOSE NOT CHANGED" if serious == "No" else "DOSE REDUCED",

            # Site
            "SITEID": adsl_rec.get("SITEID")
        }

        adae_records.append(adae_record)

    return adae_records


def generate_bds_vitals(
    vitals_data: List[Dict[str, Any]],
    adsl_data: List[Dict[str, Any]],
    study_id: str = "STUDY001"
) -> List[Dict[str, Any]]:
    """
    Generate BDS (Basic Data Structure) for vitals data.

    BDS is used for continuous variables like labs and vitals.

    Args:
        vitals_data: List of vitals records
        adsl_data: ADSL data for subject-level info
        study_id: Study identifier

    Returns:
        List of BDS records
    """
    bds_records = []

    # Convert ADSL to dict
    adsl_dict = {rec["SUBJID"]: rec for rec in adsl_data}

    # Convert vitals to long format (one row per parameter)
    vital_params = [
        ("SYSBP", "Systolic Blood Pressure", "SystolicBP", "mmHg"),
        ("DIABP", "Diastolic Blood Pressure", "DiastolicBP", "mmHg"),
        ("HR", "Heart Rate", "HeartRate", "beats/min"),
        ("TEMP", "Body Temperature", "Temperature", "C")
    ]

    record_id = 1

    for vital in vitals_data:
        subject_id = vital["SubjectID"]
        visit_name = vital["VisitName"]
        adsl_rec = adsl_dict.get(subject_id, {})

        # Determine visit number
        visit_mapping = {
            "Screening": 1,
            "Baseline": 2,
            "Week 4": 3,
            "Week 12": 4
        }
        visitnum = visit_mapping.get(visit_name, 99)

        # Get baseline values for this subject
        subject_vitals = [v for v in vitals_data if v["SubjectID"] == subject_id]
        baseline_vitals = [v for v in subject_vitals if v["VisitName"] in ["Screening", "Baseline"]]

        for paramcd, param, field, unit in vital_params:
            aval = vital.get(field)
            if aval is None:
                continue

            # Get baseline value
            if baseline_vitals:
                base = baseline_vitals[0].get(field)
            else:
                base = None

            # Calculate change from baseline
            chg = aval - base if base is not None else None

            bds_record = {
                # Identifiers
                "STUDYID": study_id,
                "USUBJID": f"{study_id}-{subject_id}",
                "SUBJID": subject_id,

                # Parameter
                "PARAMCD": paramcd,
                "PARAM": param,
                "PARAMN": {"SYSBP": 1, "DIABP": 2, "HR": 3, "TEMP": 4}[paramcd],

                # Treatment
                "TRTP": adsl_rec.get("TRT01P"),
                "TRTPN": adsl_rec.get("TRT01PN"),

                # Visit
                "VISIT": visit_name,
                "VISITNUM": visitnum,
                "ADY": None,  # Analysis day (would need dates)

                # Analysis Value
                "AVAL": round(aval, 2),
                "AVALC": str(round(aval, 2)),
                "AVALU": unit,

                # Baseline and Change
                "BASE": round(base, 2) if base else None,
                "CHG": round(chg, 2) if chg else None,
                "PCHG": round((chg / base * 100), 1) if (chg and base and base != 0) else None,

                # Analysis Flags
                "ANL01FL": "Y",
                "ABLFL": "Y" if visit_name in ["Screening", "Baseline"] else "N",
                "ITTFL": adsl_rec.get("ITTFL"),

                # Site
                "SITEID": adsl_rec.get("SITEID")
            }

            bds_records.append(bds_record)
            record_id += 1

    return bds_records


def generate_bds_labs(
    labs_data: List[Dict[str, Any]],
    adsl_data: List[Dict[str, Any]],
    study_id: str = "STUDY001"
) -> List[Dict[str, Any]]:
    """
    Generate BDS for laboratory data.

    Args:
        labs_data: List of lab records (long format)
        adsl_data: ADSL data for subject-level info
        study_id: Study identifier

    Returns:
        List of BDS lab records
    """
    bds_records = []

    # Convert ADSL to dict
    adsl_dict = {rec["SUBJID"]: rec for rec in adsl_data}

    # Get baseline for each subject/test combination
    labs_df = pd.DataFrame(labs_data)

    for idx, lab in labs_df.iterrows():
        subject_id = lab["SubjectID"]
        test_name = lab["TestName"]
        visit_name = lab["VisitName"]
        adsl_rec = adsl_dict.get(subject_id, {})

        # Get baseline for this subject/test
        baseline_labs = labs_df[
            (labs_df["SubjectID"] == subject_id) &
            (labs_df["TestName"] == test_name) &
            (labs_df["VisitName"].isin(["Baseline", "Screening"]))
        ]

        if not baseline_labs.empty:
            base = baseline_labs.iloc[0]["TestValue"]
        else:
            base = None

        aval = lab["TestValue"]
        chg = aval - base if base else None

        bds_record = {
            # Identifiers
            "STUDYID": study_id,
            "USUBJID": f"{study_id}-{subject_id}",
            "SUBJID": subject_id,

            # Parameter
            "PARAMCD": test_name.upper(),
            "PARAM": f"{test_name}",

            # Treatment
            "TRTP": adsl_rec.get("TRT01P"),
            "TRTPN": adsl_rec.get("TRT01PN"),

            # Visit
            "VISIT": visit_name,
            "VISITNUM": lab.get("VisitNum"),

            # Analysis Value
            "AVAL": round(aval, 2),
            "AVALC": str(round(aval, 2)),

            # Baseline and Change
            "BASE": round(base, 2) if base else None,
            "CHG": round(chg, 2) if chg else None,

            # Analysis Flags
            "ANL01FL": "Y",
            "ABLFL": "Y" if visit_name in ["Baseline", "Screening"] else "N",
            "ITTFL": adsl_rec.get("ITTFL"),

            # Site
            "SITEID": adsl_rec.get("SITEID")
        }

        bds_records.append(bds_record)

    return bds_records


def generate_all_adam_datasets(
    demographics_data: List[Dict[str, Any]],
    vitals_data: Optional[List[Dict[str, Any]]] = None,
    labs_data: Optional[List[Dict[str, Any]]] = None,
    ae_data: Optional[List[Dict[str, Any]]] = None,
    survival_data: Optional[List[Dict[str, Any]]] = None,
    study_id: str = "STUDY001"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate all ADaM datasets from source data.

    Args:
        demographics_data: Demographics records
        vitals_data: Vitals records
        labs_data: Labs records (long format)
        ae_data: Adverse event records
        survival_data: Survival/TTE records
        study_id: Study identifier

    Returns:
        Dict with all ADaM datasets (ADSL, ADTTE, ADAE, BDS vitals, BDS labs)
    """
    # Generate ADSL first (needed by other datasets)
    adsl = generate_adsl(
        demographics_data=demographics_data,
        vitals_data=vitals_data,
        ae_data=ae_data,
        study_id=study_id
    )

    adam_datasets = {"ADSL": adsl}

    # Generate ADTTE if survival data provided
    if survival_data:
        adtte = generate_adtte(survival_data, adsl, study_id)
        adam_datasets["ADTTE"] = adtte

    # Generate ADAE if AE data provided
    if ae_data:
        adae = generate_adae(ae_data, adsl, study_id)
        adam_datasets["ADAE"] = adae

    # Generate BDS for vitals if provided
    if vitals_data:
        bds_vitals = generate_bds_vitals(vitals_data, adsl, study_id)
        adam_datasets["BDS_VITALS"] = bds_vitals

    # Generate BDS for labs if provided
    if labs_data:
        bds_labs = generate_bds_labs(labs_data, adsl, study_id)
        adam_datasets["BDS_LABS"] = bds_labs

    return adam_datasets
