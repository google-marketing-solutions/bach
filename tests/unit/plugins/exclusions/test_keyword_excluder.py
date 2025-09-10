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
from bach.plugins.exclusions import keyword_excluder


class TestKeywordPerformance:
  def test_query_default(self):
    query = keyword_excluder.KeywordPerformance(limit=10)

    expected_query = (
      'SELECT '
      'customer.id AS customer_id, '
      'campaign.id AS campaign_id, '
      'campaign.advertising_channel_type AS campaign_type, '
      'ad_group.id AS ad_group_id, '
      'ad_group_criterion.keyword.text AS keyword, '
      'metrics.clicks AS clicks, '
      'metrics.cost_micros / 1e6 AS cost '
      'FROM keyword_view '
      'WHERE '
      "segments.date BETWEEN '2025-01-01' AND '2025-01-31' "
      'AND metrics.clicks > 0 '
      'AND metrics.impressions > 0 '
      'AND metrics.cost_micros > 0 '
      'LIMIT 10'
    )
    assert query.query == expected_query

  def test_query_metrics(self):
    query = keyword_excluder.KeywordPerformance(
      limit=10,
      metrics=['metrics.conversions AS conversions'],
    )

    expected_query = (
      'SELECT '
      'customer.id AS customer_id, '
      'campaign.id AS campaign_id, '
      'campaign.advertising_channel_type AS campaign_type, '
      'ad_group.id AS ad_group_id, '
      'ad_group_criterion.keyword.text AS keyword, '
      'metrics.clicks AS clicks, '
      'metrics.cost_micros / 1e6 AS cost, '
      'metrics.conversions AS conversions '
      'FROM keyword_view '
      'WHERE '
      "segments.date BETWEEN '2025-01-01' AND '2025-01-31' "
      'AND metrics.clicks > 0 '
      'AND metrics.impressions > 0 '
      'AND metrics.cost_micros > 0 '
      'LIMIT 10'
    )
    assert query.query == expected_query

  def test_query_dimensions(self):
    query = keyword_excluder.KeywordPerformance(
      limit=10,
      dimensions=['campaign.name AS campaign_name'],
    )

    expected_query = (
      'SELECT '
      'customer.id AS customer_id, '
      'campaign.id AS campaign_id, '
      'campaign.advertising_channel_type AS campaign_type, '
      'ad_group.id AS ad_group_id, '
      'ad_group_criterion.keyword.text AS keyword, '
      'campaign.name AS campaign_name, '
      'metrics.clicks AS clicks, '
      'metrics.cost_micros / 1e6 AS cost '
      'FROM keyword_view '
      'WHERE '
      "segments.date BETWEEN '2025-01-01' AND '2025-01-31' "
      'AND metrics.clicks > 0 '
      'AND metrics.impressions > 0 '
      'AND metrics.cost_micros > 0 '
      'LIMIT 10'
    )
    assert query.query == expected_query
