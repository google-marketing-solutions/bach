You can use `bach` in one of the following forms:

* CLI tool - use `bach` utility in your terminal or shell scripts.
* Python library - import `bach` library to use in your Python code.
* API endpoint - start FastAPI endpoint with `python -m bach.entrypoints.server`

## Example


/// tab | cli

```bash
bach run --area placement_performance \
  --rule 'clicks > 10'
  --accounts GOOGLE_ACCOUNT_ID \
  --area.exclusion_level=AD_GROUP
```
///

/// tab | python

```python
import bach

bach = Bach()

request = bach.BachRequest(
  area='placement_performance',
  rule='clicks > 10',
  accounts=['GOOGLE_ACCOUNT_ID'],
  area_parameters={
    'exclusion_level': 'AD_GROUP',
  },
)
bach.play(request)
```
///

/// tab | curl
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "area": "placement_performance",
  "rule": "clicks > 10",
  "accounts": [
    "GOOGLE_ACCOUNT_ID"
  ]
}'
```
///
