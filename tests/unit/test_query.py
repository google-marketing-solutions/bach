# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from bach import query


class TestBachQuery:
  def test_init_returns_without_filters(self):
    parameters = query.BachQueryParameters(
      resource='campaign',
      metrics=[
        'metrics.clicks AS clicks',
      ],
      dimensions=[
        'campaign.id AS campaign_id',
      ],
    )
    test_query = query.BachQuery(parameters)

    assert test_query.query_text == (
      'SELECT campaign.id AS campaign_id, metrics.clicks AS clicks '
      'FROM campaign'
    )

  def test_init_returns_nonempty_attributes(self):
    parameters = query.BachQueryParameters(
      resource='campaign',
      metrics=[
        'metrics.clicks AS clicks',
      ],
      dimensions=[
        'campaign.id AS campaign_id',
      ],
      filters=[
        'metrics.clicks > 0',
      ],
    )
    test_query = query.BachQuery(parameters)

    assert test_query.query_text == (
      'SELECT campaign.id AS campaign_id, metrics.clicks AS clicks '
      'FROM campaign WHERE metrics.clicks > 0'
    )

  def test_init_returns_multiple_attributes(self):
    parameters = query.BachQueryParameters(
      resource='campaign',
      metrics=[
        'metrics.clicks AS clicks',
        'metrics.impressions AS impressions',
      ],
      dimensions=[
        'campaign.id AS campaign_id',
        'segments.date AS date',
      ],
      filters=[
        'metrics.clicks > 0',
        'metrics.impressions > 10',
      ],
      limit=10,
    )
    test_query = query.BachQuery(parameters)

    assert test_query.query_text == (
      'SELECT campaign.id AS campaign_id, segments.date AS date, '
      'metrics.clicks AS clicks, metrics.impressions AS impressions '
      'FROM campaign '
      'WHERE metrics.clicks > 0 AND metrics.impressions > 10 '
      'LIMIT 10'
    )

  def test_init_returns_multiple_attributes_with_period(self):
    parameters = query.BachQueryParameters(
      resource='campaign',
      metrics=[
        'metrics.clicks AS clicks',
        'metrics.impressions AS impressions',
      ],
      dimensions=[
        'campaign.id AS campaign_id',
        'segments.date AS date',
      ],
      filters=[
        'metrics.clicks > 0',
        'metrics.impressions > 10',
      ],
      period={'start_date': '2025-01-01', 'end_date': '2025-01-31'},
      limit=10,
    )
    test_query = query.BachQuery(parameters)

    assert test_query.query_text == (
      'SELECT campaign.id AS campaign_id, segments.date AS date, '
      'metrics.clicks AS clicks, metrics.impressions AS impressions '
      'FROM campaign '
      "WHERE segments.date BETWEEN '2025-01-01' AND '2025-01-31' "
      'AND metrics.clicks > 0 AND metrics.impressions > 10 '
      'LIMIT 10'
    )

  def test_init_returns_multiple_attributes_with_sorts(self):
    parameters = query.BachQueryParameters(
      resource='campaign',
      metrics=[
        'metrics.clicks AS clicks',
        'metrics.impressions AS impressions',
      ],
      dimensions=[
        'campaign.id AS campaign_id',
        'segments.date AS date',
      ],
      filters=[
        'metrics.clicks > 0',
        'metrics.impressions > 10',
      ],
      period={'start_date': '2025-01-01', 'end_date': '2025-01-31'},
      sorts='metrics.clicks',
      limit=10,
    )
    test_query = query.BachQuery(parameters)

    assert test_query.query_text == (
      'SELECT campaign.id AS campaign_id, segments.date AS date, '
      'metrics.clicks AS clicks, metrics.impressions AS impressions '
      'FROM campaign '
      "WHERE segments.date BETWEEN '2025-01-01' AND '2025-01-31' "
      'AND metrics.clicks > 0 AND metrics.impressions > 10 '
      'ORDER BY metrics.clicks DESC '
      'LIMIT 10'
    )
