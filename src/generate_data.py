import pandas as pd
import numpy as np
from datetime import date, timedelta
import random

np.random.seed(42)
random.seed(42)

N_CLAIMS = 15000

states = ['CA','TX','FL','NY','IL','PA','OH','GA','NC','MI','NJ','VA','WA','AZ','TN']
_sw = [0.15,0.12,0.10,0.10,0.06,0.05,0.05,0.05,0.05,0.04,0.04,0.04,0.04,0.04,0.03]
sw = [x/sum(_sw) for x in _sw]

claim_types = ['Inpatient','Outpatient','Emergency','Pharmacy','Mental Health','Dental','Vision']
ct_weights  = [0.18,0.30,0.15,0.20,0.08,0.06,0.03]

diagnosis_codes = ['Z00.00','J18.9','I10','E11.9','M54.5','K21.0','F32.9',
                   'N18.3','J44.1','S72.001','G43.909','R51','J06.9','K92.1','I25.10']
providers = [f'PRV{str(i).zfill(4)}' for i in range(1, 201)]

start_date = date(2022, 1, 1)
delta_days  = (date(2024, 12, 31) - start_date).days

ages      = np.clip(np.random.normal(45, 15, N_CLAIMS).astype(int), 18, 85)
genders   = np.random.choice(['M','F'], N_CLAIMS, p=[0.48,0.52])
plan_types= np.random.choice(['HMO','PPO','EPO','HDHP'], N_CLAIMS, p=[0.35,0.30,0.20,0.15])

claim_dates = [start_date + timedelta(days=random.randint(0, delta_days)) for _ in range(N_CLAIMS)]
claim_type_arr = np.random.choice(claim_types, N_CLAIMS, p=ct_weights)

# billed amount by claim type
base_amounts = {'Inpatient':18000,'Outpatient':1200,'Emergency':4500,
                'Pharmacy':280,'Mental Health':350,'Dental':600,'Vision':180}
billed = []
for ct in claim_type_arr:
    base = base_amounts[ct]
    billed.append(round(max(50, np.random.lognormal(np.log(base), 0.6)), 2))

# allowed = billed * factor by plan
allowed = []
for b, pt in zip(billed, plan_types):
    factor = {'HMO':0.72,'PPO':0.81,'EPO':0.75,'HDHP':0.68}[pt]
    allowed.append(round(b * factor * np.random.uniform(0.9, 1.1), 2))

# denial logic
def denial_prob(ct, plan, age, diag):
    base = {'Inpatient':0.08,'Outpatient':0.12,'Emergency':0.05,
            'Pharmacy':0.18,'Mental Health':0.22,'Dental':0.15,'Vision':0.10}[ct]
    if plan == 'HDHP': base *= 1.35
    if plan == 'HMO':  base *= 1.20
    if age > 65: base *= 0.85
    if diag in ['F32.9','G43.909']: base *= 1.40
    return min(base, 0.60)

diag_arr     = np.random.choice(diagnosis_codes, N_CLAIMS)
provider_arr = np.random.choice(providers, N_CLAIMS,
               p=[1/200]*200)
state_arr    = np.random.choice(states, N_CLAIMS, p=sw)

statuses = []
paid_amounts = []
denial_reasons = ['Medical Necessity','Out of Network','Prior Auth Required',
                  'Duplicate Claim','Coverage Lapsed','Coding Error']

for i in range(N_CLAIMS):
    dp = denial_prob(claim_type_arr[i], plan_types[i], ages[i], diag_arr[i])
    r  = np.random.random()
    if r < dp:
        statuses.append('Denied')
        paid_amounts.append(0.0)
    elif r < dp + 0.08:
        statuses.append('Pending')
        paid_amounts.append(0.0)
    elif r < dp + 0.10:
        statuses.append('Partial')
        paid_amounts.append(round(allowed[i] * np.random.uniform(0.3, 0.7), 2))
    else:
        statuses.append('Approved')
        paid_amounts.append(round(allowed[i] * np.random.uniform(0.80, 0.95), 2))

denial_reason_arr = [random.choice(denial_reasons) if s == 'Denied' else '' for s in statuses]

claims = pd.DataFrame({
    'claim_id':      [f'C{str(i).zfill(6)}' for i in range(1, N_CLAIMS+1)],
    'claim_date':    claim_dates,
    'claim_type':    claim_type_arr,
    'diagnosis_code':diag_arr,
    'provider_id':   provider_arr,
    'patient_age':   ages,
    'patient_gender':genders,
    'plan_type':     plan_types,
    'state':         state_arr,
    'billed_amount': billed,
    'allowed_amount':allowed,
    'paid_amount':   paid_amounts,
    'status':        statuses,
    'denial_reason': denial_reason_arr,
})
claims.to_csv('data/raw/claims.csv', index=False)
print("Done.")
print(claims['status'].value_counts())
print(f"\nTotal billed: ${claims['billed_amount'].sum():,.0f}")
print(f"Total paid:   ${claims['paid_amount'].sum():,.0f}")