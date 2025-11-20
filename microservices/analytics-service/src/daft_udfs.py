"""
Daft User-Defined Functions (UDFs) - Custom medical data processing functions
Provides domain-specific UDFs for clinical trial data analysis
"""
import daft
from daft import udf, DataType
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass


class MedicalUDFs:
    """
    Collection of medical-specific User-Defined Functions for Daft
    """

    @staticmethod
    @udf(return_dtype=DataType.float64())
    def calculate_pulse_pressure(systolic: pd.Series, diastolic: pd.Series) -> pd.Series:
        """
        Calculate pulse pressure (PP = SBP - DBP)

        Args:
            systolic: Systolic blood pressure
            diastolic: Diastolic blood pressure

        Returns:
            Pulse pressure
        """
        return systolic - diastolic

    @staticmethod
    @udf(return_dtype=DataType.float64())
    def calculate_map(systolic: pd.Series, diastolic: pd.Series) -> pd.Series:
        """
        Calculate Mean Arterial Pressure (MAP = DBP + 1/3 * PP)

        Args:
            systolic: Systolic blood pressure
            diastolic: Diastolic blood pressure

        Returns:
            Mean arterial pressure
        """
        pulse_pressure = systolic - diastolic
        return diastolic + (pulse_pressure / 3)

    @staticmethod
    @udf(return_dtype=DataType.string())
    def categorize_blood_pressure(systolic: pd.Series, diastolic: pd.Series) -> pd.Series:
        """
        Categorize blood pressure according to AHA guidelines

        Categories:
        - Normal: SBP < 120 and DBP < 80
        - Elevated: SBP 120-129 and DBP < 80
        - Stage 1 Hypertension: SBP 130-139 or DBP 80-89
        - Stage 2 Hypertension: SBP >= 140 or DBP >= 90

        Args:
            systolic: Systolic blood pressure
            diastolic: Diastolic blood pressure

        Returns:
            Blood pressure category
        """
        categories = []
        for sbp, dbp in zip(systolic, diastolic):
            if sbp < 120 and dbp < 80:
                categories.append('Normal')
            elif 120 <= sbp < 130 and dbp < 80:
                categories.append('Elevated')
            elif (130 <= sbp < 140) or (80 <= dbp < 90):
                categories.append('Stage1_Hypertension')
            else:
                categories.append('Stage2_Hypertension')
        return pd.Series(categories)

    @staticmethod
    @udf(return_dtype=DataType.string())
    def categorize_heart_rate(heart_rate: pd.Series) -> pd.Series:
        """
        Categorize heart rate

        Categories:
        - Bradycardia: HR < 60
        - Normal: HR 60-100
        - Tachycardia: HR > 100

        Args:
            heart_rate: Heart rate in bpm

        Returns:
            Heart rate category
        """
        categories = []
        for hr in heart_rate:
            if hr < 60:
                categories.append('Bradycardia')
            elif hr <= 100:
                categories.append('Normal')
            else:
                categories.append('Tachycardia')
        return pd.Series(categories)

    @staticmethod
    @udf(return_dtype=DataType.string())
    def categorize_temperature(temperature: pd.Series) -> pd.Series:
        """
        Categorize body temperature

        Categories:
        - Hypothermia: < 35.0°C
        - Normal: 35.0-37.5°C
        - Fever: 37.5-38.3°C
        - High Fever: > 38.3°C

        Args:
            temperature: Body temperature in Celsius

        Returns:
            Temperature category
        """
        categories = []
        for temp in temperature:
            if temp < 35.0:
                categories.append('Hypothermia')
            elif temp <= 37.5:
                categories.append('Normal')
            elif temp <= 38.3:
                categories.append('Fever')
            else:
                categories.append('High_Fever')
        return pd.Series(categories)

    @staticmethod
    @udf(return_dtype=DataType.bool())
    def is_vital_sign_abnormal(systolic: pd.Series, diastolic: pd.Series,
                               heart_rate: pd.Series, temperature: pd.Series) -> pd.Series:
        """
        Check if any vital sign is abnormal

        Abnormal ranges:
        - SBP: < 90 or > 180
        - DBP: < 60 or > 120
        - HR: < 50 or > 120
        - Temp: < 35.0 or > 38.5

        Args:
            systolic: Systolic BP
            diastolic: Diastolic BP
            heart_rate: Heart rate
            temperature: Temperature

        Returns:
            Boolean indicating if any vital is abnormal
        """
        abnormal = []
        for sbp, dbp, hr, temp in zip(systolic, diastolic, heart_rate, temperature):
            is_abnormal = (
                sbp < 90 or sbp > 180 or
                dbp < 60 or dbp > 120 or
                hr < 50 or hr > 120 or
                temp < 35.0 or temp > 38.5
            )
            abnormal.append(is_abnormal)
        return pd.Series(abnormal)

    @staticmethod
    @udf(return_dtype=DataType.int64())
    def calculate_cardiovascular_risk_score(systolic: pd.Series, diastolic: pd.Series,
                                            heart_rate: pd.Series) -> pd.Series:
        """
        Calculate a simple cardiovascular risk score (0-10)
        Higher score indicates higher risk

        Args:
            systolic: Systolic BP
            diastolic: Diastolic BP
            heart_rate: Heart rate

        Returns:
            Risk score (0-10)
        """
        risk_scores = []
        for sbp, dbp, hr in zip(systolic, diastolic, heart_rate):
            score = 0

            # Systolic BP contribution
            if sbp >= 180:
                score += 4
            elif sbp >= 160:
                score += 3
            elif sbp >= 140:
                score += 2
            elif sbp >= 130:
                score += 1

            # Diastolic BP contribution
            if dbp >= 110:
                score += 3
            elif dbp >= 100:
                score += 2
            elif dbp >= 90:
                score += 1

            # Heart rate contribution
            if hr >= 100:
                score += 2
            elif hr < 50:
                score += 1
            elif hr >= 90:
                score += 1

            risk_scores.append(min(score, 10))  # Cap at 10

        return pd.Series(risk_scores)

    @staticmethod
    def apply_baseline_change(df: daft.DataFrame, endpoint: str = 'SystolicBP') -> pd.DataFrame:
        """
        Apply UDF to calculate change from baseline

        Args:
            df: Daft DataFrame
            endpoint: Vital sign to calculate change for

        Returns:
            Pandas DataFrame with change from baseline
        """
        pdf = df.to_pandas()

        # Get baseline values
        baseline = pdf[pdf['VisitName'] == 'Screening'][['SubjectID', endpoint]]
        baseline = baseline.rename(columns={endpoint: f'Baseline{endpoint}'})

        # Merge and calculate change
        merged = pdf.merge(baseline, on='SubjectID', how='left')
        merged[f'Change{endpoint}'] = merged[endpoint] - merged[f'Baseline{endpoint}']

        return merged

    @staticmethod
    @udf(return_dtype=DataType.float64())
    def normalize_vital_sign(values: pd.Series) -> pd.Series:
        """
        Normalize vital sign values to 0-1 range using min-max normalization

        Args:
            values: Vital sign values

        Returns:
            Normalized values
        """
        min_val = values.min()
        max_val = values.max()
        if max_val - min_val == 0:
            return pd.Series([0.5] * len(values))
        return (values - min_val) / (max_val - min_val)

    @staticmethod
    @udf(return_dtype=DataType.float64())
    def standardize_vital_sign(values: pd.Series) -> pd.Series:
        """
        Standardize vital sign values to z-scores

        Args:
            values: Vital sign values

        Returns:
            Standardized values (z-scores)
        """
        mean = values.mean()
        std = values.std()
        if std == 0:
            return pd.Series([0.0] * len(values))
        return (values - mean) / std

    @staticmethod
    @udf(return_dtype=DataType.bool())
    def detect_measurement_error(systolic: pd.Series, diastolic: pd.Series) -> pd.Series:
        """
        Detect potential measurement errors in blood pressure

        Errors include:
        - SBP <= DBP
        - Pulse pressure < 20 or > 100
        - Extreme values

        Args:
            systolic: Systolic BP
            diastolic: Diastolic BP

        Returns:
            Boolean indicating potential error
        """
        errors = []
        for sbp, dbp in zip(systolic, diastolic):
            pulse_pressure = sbp - dbp
            has_error = (
                sbp <= dbp or  # Invalid relationship
                pulse_pressure < 20 or  # Too narrow
                pulse_pressure > 100 or  # Too wide
                sbp < 70 or sbp > 250 or  # Extreme SBP
                dbp < 40 or dbp > 150  # Extreme DBP
            )
            errors.append(has_error)
        return pd.Series(errors)

    @staticmethod
    @udf(return_dtype=DataType.string())
    def determine_intervention_needed(systolic: pd.Series, diastolic: pd.Series,
                                     heart_rate: pd.Series, temperature: pd.Series) -> pd.Series:
        """
        Determine if clinical intervention is needed based on vitals

        Categories:
        - Urgent: Immediate intervention needed
        - Monitor: Close monitoring required
        - Normal: No intervention needed

        Args:
            systolic: Systolic BP
            diastolic: Diastolic BP
            heart_rate: Heart rate
            temperature: Temperature

        Returns:
            Intervention level
        """
        interventions = []
        for sbp, dbp, hr, temp in zip(systolic, diastolic, heart_rate, temperature):
            # Urgent criteria
            if (sbp >= 180 or sbp < 90 or
                dbp >= 120 or dbp < 60 or
                hr >= 120 or hr < 50 or
                temp >= 39.0 or temp < 35.0):
                interventions.append('Urgent')
            # Monitor criteria
            elif (sbp >= 140 or sbp < 100 or
                  dbp >= 90 or dbp < 70 or
                  hr >= 100 or hr < 60 or
                  temp >= 38.0 or temp < 36.0):
                interventions.append('Monitor')
            else:
                interventions.append('Normal')
        return pd.Series(interventions)

    @staticmethod
    @udf(return_dtype=DataType.float64())
    def calculate_shock_index(heart_rate: pd.Series, systolic: pd.Series) -> pd.Series:
        """
        Calculate Shock Index (SI = HR / SBP)
        Normal: 0.5-0.7
        Elevated: > 0.9 suggests hypovolemia

        Args:
            heart_rate: Heart rate
            systolic: Systolic BP

        Returns:
            Shock index
        """
        return heart_rate / systolic

    @staticmethod
    @udf(return_dtype=DataType.int64())
    def calculate_visit_number(visit_name: pd.Series) -> pd.Series:
        """
        Convert visit name to numeric visit number

        Args:
            visit_name: Visit name

        Returns:
            Visit number
        """
        visit_map = {
            'Screening': 0,
            'Day 1': 1,
            'Week 4': 2,
            'Week 12': 3
        }
        return pd.Series([visit_map.get(v, -1) for v in visit_name])

    @staticmethod
    @udf(return_dtype=DataType.int64())
    def calculate_days_from_baseline(visit_name: pd.Series) -> pd.Series:
        """
        Calculate approximate days from baseline visit

        Args:
            visit_name: Visit name

        Returns:
            Days from baseline
        """
        days_map = {
            'Screening': 0,
            'Day 1': 1,
            'Week 4': 28,
            'Week 12': 84
        }
        return pd.Series([days_map.get(v, -1) for v in visit_name])

    @staticmethod
    def apply_quality_flags(df: daft.DataFrame) -> pd.DataFrame:
        """
        Apply quality control flags to the data

        Args:
            df: Daft DataFrame

        Returns:
            Pandas DataFrame with quality flags
        """
        pdf = df.to_pandas()

        # Initialize flags
        pdf['QC_BP_Error'] = False
        pdf['QC_Abnormal_Vitals'] = False
        pdf['QC_Intervention_Needed'] = False

        # Apply flags
        for idx, row in pdf.iterrows():
            # BP measurement error
            pulse_pressure = row['SystolicBP'] - row['DiastolicBP']
            if (row['SystolicBP'] <= row['DiastolicBP'] or
                pulse_pressure < 20 or pulse_pressure > 100):
                pdf.at[idx, 'QC_BP_Error'] = True

            # Abnormal vitals
            if (row['SystolicBP'] < 90 or row['SystolicBP'] > 180 or
                row['DiastolicBP'] < 60 or row['DiastolicBP'] > 120 or
                row['HeartRate'] < 50 or row['HeartRate'] > 120 or
                row['Temperature'] < 35.0 or row['Temperature'] > 38.5):
                pdf.at[idx, 'QC_Abnormal_Vitals'] = True

            # Intervention needed
            if (row['SystolicBP'] >= 180 or row['SystolicBP'] < 90 or
                row['DiastolicBP'] >= 120 or row['DiastolicBP'] < 60 or
                row['HeartRate'] >= 120 or row['HeartRate'] < 50 or
                row['Temperature'] >= 39.0 or row['Temperature'] < 35.0):
                pdf.at[idx, 'QC_Intervention_Needed'] = True

        return pdf


class AdvancedMedicalUDFs:
    """
    Advanced UDFs for complex medical data analysis
    """

    @staticmethod
    def calculate_dose_response(df: daft.DataFrame, dose_column: str = 'Dose',
                                 response_column: str = 'SystolicBP') -> pd.DataFrame:
        """
        Calculate dose-response relationship

        Args:
            df: Daft DataFrame
            dose_column: Column with dose information
            response_column: Column with response measurement

        Returns:
            Pandas DataFrame with dose-response analysis
        """
        pdf = df.to_pandas()

        # Group by dose and calculate mean response
        dose_response = pdf.groupby(dose_column)[response_column].agg(['mean', 'std', 'count'])
        dose_response['se'] = dose_response['std'] / np.sqrt(dose_response['count'])

        return dose_response.reset_index()

    @staticmethod
    def identify_treatment_responders(df: daft.DataFrame, threshold: float = -10.0,
                                     endpoint: str = 'SystolicBP') -> pd.DataFrame:
        """
        Identify treatment responders

        Args:
            df: Daft DataFrame
            threshold: Threshold for response (e.g., -10 mmHg)
            endpoint: Endpoint to evaluate

        Returns:
            Pandas DataFrame with responder status
        """
        pdf = df.to_pandas()

        # Calculate change from baseline
        baseline = pdf[pdf['VisitName'] == 'Screening'][['SubjectID', endpoint]]
        baseline = baseline.rename(columns={endpoint: f'Baseline{endpoint}'})

        merged = pdf.merge(baseline, on='SubjectID', how='left')
        merged[f'Change{endpoint}'] = merged[endpoint] - merged[f'Baseline{endpoint}']

        # Determine responder status
        merged['IsResponder'] = merged[f'Change{endpoint}'] <= threshold

        return merged
