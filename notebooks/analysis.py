import pandas as pd
import numpy as np
import os

claims = pd.read_csv('data/raw/claims.csv', parse_dates=['claim_date'])

claims['is_denied']   = (claims['status'] == 'Denied').astype(int)
claims['is_approved'] = (claims['status'] == 'Approved').astype(int)
claims['year']        = claims['claim_date'].dt.year
claims['month']       = claims['claim_date'].dt.month
claims['yr_month']    = claims['claim_date'].dt.to_period('M').astype(str)
claims['age_band']    = pd.cut(claims['patient_age'],
                               bins=[17,30,45,60,75,85],
                               labels=['18-30','31-45','46-60','61-75','76+'])

os.makedirs('data/processed', exist_ok=True)

# 1. master
claims.to_csv('data/processed/master_claims.csv', index=False)

# 2. by claim type
claims.groupby('claim_type').agg(
    total_claims    = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
    total_paid      = ('paid_amount','sum'),
    avg_billed      = ('billed_amount','mean'),
    avg_paid        = ('paid_amount','mean'),
    denial_rate     = ('is_denied','mean'),
).reset_index().assign(denial_rate=lambda x: x['denial_rate']*100
).sort_values('total_billed', ascending=False
).to_csv('data/processed/by_claim_type.csv', index=False)

# 3. by plan type
claims.groupby('plan_type').agg(
    total_claims    = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
    total_paid      = ('paid_amount','sum'),
    denial_rate     = ('is_denied','mean'),
    avg_billed      = ('billed_amount','mean'),
).reset_index().assign(denial_rate=lambda x: x['denial_rate']*100
).to_csv('data/processed/by_plan_type.csv', index=False)

# 4. by status
claims.groupby('status').agg(
    count           = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
    total_paid      = ('paid_amount','sum'),
).reset_index().assign(
    pct             = lambda x: x['count']/x['count'].sum()*100
).to_csv('data/processed/by_status.csv', index=False)

# 5. denial reasons
claims[claims['status']=='Denied'].groupby('denial_reason').agg(
    count           = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
).reset_index().assign(
    pct             = lambda x: x['count']/x['count'].sum()*100
).sort_values('count', ascending=False
).to_csv('data/processed/denial_reasons.csv', index=False)

# 6. monthly trend
claims.groupby('yr_month').agg(
    total_claims    = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
    total_paid      = ('paid_amount','sum'),
    denial_rate     = ('is_denied','mean'),
).reset_index().assign(denial_rate=lambda x: x['denial_rate']*100
).to_csv('data/processed/monthly_trend.csv', index=False)

# 7. by state
claims.groupby('state').agg(
    total_claims    = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
    denial_rate     = ('is_denied','mean'),
    avg_billed      = ('billed_amount','mean'),
).reset_index().assign(denial_rate=lambda x: x['denial_rate']*100
).to_csv('data/processed/by_state.csv', index=False)

# 8. top providers by billed
claims.groupby('provider_id').agg(
    total_claims    = ('claim_id','count'),
    total_billed    = ('billed_amount','sum'),
    total_paid      = ('paid_amount','sum'),
    denial_rate     = ('is_denied','mean'),
    avg_billed      = ('billed_amount','mean'),
).reset_index().assign(denial_rate=lambda x: x['denial_rate']*100
).sort_values('total_billed', ascending=False
).head(50).to_csv('data/processed/top_providers.csv', index=False)

# 9. by age band
claims.groupby('age_band', observed=True).agg(
    total_claims    = ('claim_id','count'),
    avg_billed      = ('billed_amount','mean'),
    denial_rate     = ('is_denied','mean'),
).reset_index().assign(denial_rate=lambda x: x['denial_rate']*100
).to_csv('data/processed/by_age_band.csv', index=False)

print("All CSVs saved.")
print(f"\nDenial rate: {claims['is_denied'].mean()*100:.1f}%")
print(f"Total billed: ${claims['billed_amount'].sum():,.0f}")
print(f"Total paid:   ${claims['paid_amount'].sum():,.0f}")
print(f"\nTop denial reasons:")
print(claims[claims['status']=='Denied']['denial_reason'].value_counts())