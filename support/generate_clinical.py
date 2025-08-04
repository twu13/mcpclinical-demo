import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import Boolean, DateTime, Integer, String, create_engine

# Set random seed for reproducibility
np.random.seed(123)
n = 2000

# Generate random dates within the past year
today = datetime.now().date()
random_days = np.random.choice(range(0, 365), size=n, replace=True)
enrollment_dates = [today - timedelta(days=int(days)) for days in random_days]

# Create subject IDs
subject_ids = [f"001-{i:04d}" for i in range(1, n + 1)]

# Generate site IDs
site_ids = [f"SITE{i:02d}" for i in range(1, 26)]
random_sites = np.random.choice(site_ids, size=n, replace=True)

# Simple evaluability logic - 80% chance of being evaluable
eval_flags = np.random.binomial(1, 0.80, size=n).astype(bool)

# Generate other demographic data
ages = np.random.choice(range(18, 86), size=n, replace=True)
sexes = np.random.choice(["M", "F"], size=n, replace=True)
races = np.random.choice(["White", "Black", "Asian", "Other"], size=n, replace=True)

clinical_data = pd.DataFrame(
    {
        "STUDYID": ["DEMO-101"] * n,
        "USUBJID": subject_ids,
        "SITEID": random_sites,
        "ENRLDT": enrollment_dates,
        "EVALFLAG": eval_flags,
        "AGE": ages,
        "SEX": sexes,
        "RACE": races,
    }
)

# Set database path in the project root directory
db_file = "clinical.db"

# Check if database exists
if os.path.exists(db_file):
    print(f"{db_file} already exists. Skipping database creation.")
else:
    # Create SQLAlchemy engine
    engine = create_engine(f"sqlite:///{db_file}")

    # Define column types explicitly for all columns
    dtype_mapping = {
        "STUDYID": String,
        "USUBJID": String,
        "SITEID": String,
        "ENRLDT": DateTime,
        "EVALFLAG": Boolean,
        "AGE": Integer,
        "SEX": String,
        "RACE": String,
    }

    clinical_data.to_sql("clinical", engine, if_exists="replace", index=False, dtype=dtype_mapping)

    print(f"Generated {n} subject records and saved to {db_file}")
