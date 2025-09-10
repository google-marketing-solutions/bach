## GAQL queries

You can provide GQAL query.

```sql
SELECT
  campaign.id AS campaign_id,
  metrics.clics AS clicks
FROM campaign
WHERE
  segments.date BETWEEN "{start_date}" AND "{end_date}"
```


```bash
bach run --query query.sql \
  --rule 'clicks > 10' \
  --account GOOGLE_ACCOUNT_ID
```

## Builder queries

For complex scenarios you can work with `bach.query.BachQuery` class.

```python
from typing import ClassVar
from bach import BachQuery

class MyQuery(BachQuery):
  name: ClassVar[str] = 'my_query'
  resource: str = 'campaign'
  metrics: list[str] = ['clicks', 'impressions', 'cost', 'conversions']
  dimensions: list[str] = ['campaign.name', 'ad_group.id', 'ad_group.name']
  filters: list[str] = ['metrics.clicks > 10', 'metrics.impressions > 100']
  sorts: str = 'metrics.clicks'
  limit: int = 1_000
```

```bash
bach ?
```
