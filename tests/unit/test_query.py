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
  def test_init_returns_empty_attributes(self):
    test_query = query.BachQuery()

    assert test_query.metrics == ''
    assert test_query.dimensions == ''
    assert test_query.filters == ''

  def test_init_returns_nonempty_attributes(self):
    parameters = query.BachQueryParameters(
      metrics={
        'metrics.clicks AS clicks',
      },
      dimensions={
        'campaign.id AS campaign_id',
      },
      filters={
        'metrics.clicks > 0',
      },
    )
    test_query = query.BachQuery(parameters)

    assert test_query.metrics == 'metrics.clicks AS clicks,\n'
    assert test_query.dimensions == 'campaign.id AS campaign_id,\n'
    assert test_query.filters == 'metrics.clicks > 0'

  def test_init_returns_default_attributes(self):
    parameters = query.BachQueryParameters(
      limit=10,
    )
    test_query = query.BachQuery(parameters)

    assert test_query.dimensions == 'campaign.id AS campaign,\n'
    assert test_query.metrics == ''
    assert test_query.filters == ''
