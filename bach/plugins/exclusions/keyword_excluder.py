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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

"""Performance keyword exclusions from Google Ads."""

from typing import ClassVar

import pydantic
from garf.core import report as garf_report

from bach.plugins.exclusions import base_excluder
from bach.query import BachQuery, Period


class KeywordExclusionActor(base_excluder.BaseExclusionActor):
  """Responsible for excluding keywords."""

  def _setup_criterion(
    self, entity_criterion, row: garf_report.GarfRow
  ) -> None:
    entity_criterion.negative = True
    entity_criterion.keyword.text = (
      row.search_term if hasattr(row, 'search_term') else row.keyword
    )
    entity_criterion.keyword.match_type = (
      self.client.enums.KeywordMatchTypeEnum.EXACT
    )


class BaseKeywordPerformance(BachQuery):
  entity: str
  resource: str = ''
  start_date: str = pydantic.Field(default='2025-01-01')
  end_date: str = pydantic.Field(default='2025-01-31')

  @property
  def query(self) -> str:
    common_filters = [
      'metrics.clicks > 0',
      'metrics.impressions > 0',
      'metrics.cost_micros > 0',
    ]
    common_metrics = [
      'metrics.clicks AS clicks',
      'metrics.cost_micros / 1e6 AS cost',
    ]

    common_dimensions = [
      'customer.id AS customer_id',
      'campaign.id AS campaign_id',
      'campaign.advertising_channel_type AS campaign_type',
      'ad_group.id AS ad_group_id',
      f'{self.entity} AS keyword',
    ]
    params = BachQuery(
      resource=self.resource,
      dimensions=common_dimensions + self.dimensions,
      metrics=common_metrics + self.metrics,
      filters=common_filters + self.filters,
      period=Period(start_date=self.start_date, end_date=self.end_date),
      limit=self.limit,
    )
    return params.query_text


class KeywordPerformance(BaseKeywordPerformance):
  name: ClassVar[str] = 'keyword_performance'
  resource: str = 'keyword_view'
  entity: str = 'ad_group_criterion.keyword.text'


class SearchTermPerformance(BaseKeywordPerformance):
  name: ClassVar[str] = 'search_term_performance'
  resource: str = 'search_term_view'
  entity: str = 'search_term_view.search_term'
