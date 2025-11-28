"""
Daft Data Processor - Core Daft DataFrame operations for medical data analysis
Provides distributed data processing capabilities using Daft library
"""
import daft
from daft import col, lit
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import io


class DaftMedicalDataProcessor:
    """
    Core processor for medical data using Daft distributed dataframes
    Supports lazy evaluation, distributed computing, and complex transformations
    """

    def __init__(self):
        """Initialize the Daft processor"""
        self.df: Optional[daft.DataFrame] = None

    def load_from_dict(self, data: List[Dict[str, Any]]) -> daft.DataFrame:
        """
        Load data from a list of dictionaries into a Daft DataFrame

        Args:
            data: List of dictionaries representing records

        Returns:
            Daft DataFrame
        """
        # Convert to pandas first, then to Daft
        pdf = pd.DataFrame(data)
        self.df = daft.from_pandas(pdf)
        return self.df

    def load_from_pandas(self, pdf: pd.DataFrame) -> daft.DataFrame:
        """
        Load data from a pandas DataFrame

        Args:
            pdf: Pandas DataFrame

        Returns:
            Daft DataFrame
        """
        self.df = daft.from_pandas(pdf)
        return self.df

    def load_from_csv(self, filepath: str) -> daft.DataFrame:
        """
        Load data from CSV file using Daft's native CSV reader

        Args:
            filepath: Path to CSV file

        Returns:
            Daft DataFrame
        """
        self.df = daft.read_csv(filepath)
        return self.df

    def load_from_parquet(self, filepath: str) -> daft.DataFrame:
        """
        Load data from Parquet file using Daft's native Parquet reader

        Args:
            filepath: Path to Parquet file

        Returns:
            Daft DataFrame
        """
        self.df = daft.read_parquet(filepath)
        return self.df

    def select_columns(self, columns: List[str]) -> daft.DataFrame:
        """
        Select specific columns from the DataFrame

        Args:
            columns: List of column names to select

        Returns:
            Daft DataFrame with selected columns
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.select(*[col(c) for c in columns])
        return self.df

    def filter_rows(self, condition: str, **kwargs) -> daft.DataFrame:
        """
        Filter rows based on a condition

        Args:
            condition: Filter condition (e.g., "SystolicBP > 140")
            **kwargs: Additional parameters for the filter

        Returns:
            Filtered Daft DataFrame
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # Parse simple conditions
        # Example: "SystolicBP > 140"
        parts = condition.split()
        if len(parts) == 3:
            column, operator, value = parts
            value = float(value) if '.' in value else int(value) if value.isdigit() else value.strip('"\'')

            if operator == '>':
                self.df = self.df.where(col(column) > value)
            elif operator == '>=':
                self.df = self.df.where(col(column) >= value)
            elif operator == '<':
                self.df = self.df.where(col(column) < value)
            elif operator == '<=':
                self.df = self.df.where(col(column) <= value)
            elif operator == '==':
                self.df = self.df.where(col(column) == value)
            elif operator == '!=':
                self.df = self.df.where(col(column) != value)

        return self.df

    def filter_by_treatment_arm(self, treatment_arm: str) -> daft.DataFrame:
        """
        Filter data by treatment arm

        Args:
            treatment_arm: Treatment arm (e.g., "Active", "Placebo")

        Returns:
            Filtered Daft DataFrame
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.where(col("TreatmentArm") == treatment_arm)
        return self.df

    def filter_by_visit(self, visit_name: str) -> daft.DataFrame:
        """
        Filter data by visit name

        Args:
            visit_name: Visit name (e.g., "Week 12", "Screening")

        Returns:
            Filtered Daft DataFrame
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.where(col("VisitName") == visit_name)
        return self.df

    def add_derived_column(self, column_name: str, expression: str) -> daft.DataFrame:
        """
        Add a derived column based on an expression

        Args:
            column_name: Name of the new column
            expression: Expression to compute the column

        Returns:
            Daft DataFrame with new column
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # Example expressions:
        # "SystolicBP - DiastolicBP" -> Pulse Pressure
        # "SystolicBP + DiastolicBP" -> Sum

        if " - " in expression:
            parts = expression.split(" - ")
            self.df = self.df.with_column(column_name, col(parts[0].strip()) - col(parts[1].strip()))
        elif " + " in expression:
            parts = expression.split(" + ")
            self.df = self.df.with_column(column_name, col(parts[0].strip()) + col(parts[1].strip()))
        elif " * " in expression:
            parts = expression.split(" * ")
            self.df = self.df.with_column(column_name, col(parts[0].strip()) * col(parts[1].strip()))
        elif " / " in expression:
            parts = expression.split(" / ")
            self.df = self.df.with_column(column_name, col(parts[0].strip()) / col(parts[1].strip()))

        return self.df

    def add_pulse_pressure(self) -> daft.DataFrame:
        """
        Add Pulse Pressure column (SystolicBP - DiastolicBP)

        Returns:
            Daft DataFrame with PulsePressure column
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.with_column("PulsePressure", col("SystolicBP") - col("DiastolicBP"))
        return self.df

    def add_mean_arterial_pressure(self) -> daft.DataFrame:
        """
        Add Mean Arterial Pressure column (MAP = DBP + 1/3 * Pulse Pressure)

        Returns:
            Daft DataFrame with MAP column
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # MAP = DBP + (SBP - DBP) / 3
        pulse_pressure = col("SystolicBP") - col("DiastolicBP")
        self.df = self.df.with_column("MeanArterialPressure", col("DiastolicBP") + pulse_pressure / 3)
        return self.df

    def add_hypertension_category(self) -> daft.DataFrame:
        """
        Add hypertension category based on SystolicBP
        Categories: Normal (<120), Elevated (120-129), Stage1 (130-139), Stage2 (>=140)

        Returns:
            Daft DataFrame with HypertensionCategory column
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # Daft doesn't have if-else directly, we'll use when/otherwise
        # For now, we'll convert to pandas, add the category, and convert back
        pdf = self.df.to_pandas()
        pdf['HypertensionCategory'] = pd.cut(
            pdf['SystolicBP'],
            bins=[0, 120, 130, 140, 300],
            labels=['Normal', 'Elevated', 'Stage1', 'Stage2']
        )
        self.df = daft.from_pandas(pdf)
        return self.df

    def sort_by(self, columns: List[str], ascending: bool = True) -> daft.DataFrame:
        """
        Sort DataFrame by columns

        Args:
            columns: List of column names to sort by
            ascending: Sort in ascending order

        Returns:
            Sorted Daft DataFrame
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # Daft's sort
        for column in columns:
            if ascending:
                self.df = self.df.sort(col(column))
            else:
                self.df = self.df.sort(col(column), desc=True)

        return self.df

    def limit(self, n: int) -> daft.DataFrame:
        """
        Limit the number of rows

        Args:
            n: Number of rows to keep

        Returns:
            Limited Daft DataFrame
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.limit(n)
        return self.df

    def collect(self) -> pd.DataFrame:
        """
        Execute the lazy operations and collect results as pandas DataFrame

        Returns:
            Pandas DataFrame with results
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        return self.df.to_pandas()

    def show(self, n: int = 10) -> None:
        """
        Display first n rows

        Args:
            n: Number of rows to display
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df.limit(n).show()

    def get_schema(self) -> Dict[str, str]:
        """
        Get the schema of the DataFrame

        Returns:
            Dictionary mapping column names to types
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        schema = self.df.schema()
        return {field.name: str(field.dtype) for field in schema}

    def count_rows(self) -> int:
        """
        Count the number of rows in the DataFrame

        Returns:
            Number of rows
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        return len(self.df.to_pandas())

    def distinct(self, columns: List[str]) -> daft.DataFrame:
        """
        Get distinct values for specified columns

        Args:
            columns: List of column names

        Returns:
            Daft DataFrame with distinct values
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.select(*[col(c) for c in columns]).distinct()
        return self.df

    def join(self, other_df: daft.DataFrame, on: str, how: str = "inner") -> daft.DataFrame:
        """
        Join with another DataFrame

        Args:
            other_df: Another Daft DataFrame
            on: Column to join on
            how: Join type ("inner", "left", "right", "outer")

        Returns:
            Joined Daft DataFrame
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        self.df = self.df.join(other_df, on=on, how=how)
        return self.df

    def export_to_csv(self, filepath: str) -> None:
        """
        Export DataFrame to CSV file

        Args:
            filepath: Output file path
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # Convert to pandas and export
        pdf = self.df.to_pandas()
        pdf.to_csv(filepath, index=False)

    def export_to_parquet(self, filepath: str) -> None:
        """
        Export DataFrame to Parquet file

        Args:
            filepath: Output file path
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        # Daft's native parquet write
        self.df.write_parquet(filepath)

    def get_execution_plan(self) -> str:
        """
        Get the execution plan for the current DataFrame
        Useful for understanding lazy evaluation

        Returns:
            Execution plan as string
        """
        if self.df is None:
            raise ValueError("DataFrame not loaded. Call load_from_* first.")

        return str(self.df.explain(show_all=True))
