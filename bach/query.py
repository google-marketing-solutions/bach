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

import datetime
from typing import Sequence

import pydantic
from garf_core import base_query

from bach import exclusion_specification

METRICS = [
  'clicks',
  'impressions',
  'cost',
  'conversions',
  'video_views',
  'interactions',
  'all_conversions',
  'view_through_conversions',
]

COMPOUND_METRICS = {
  'ctr': ['clicks', 'impressions'],
  'avg_cpc': ['cost', 'clicks'],
  'avg_cpm': ['cost', 'impressions'],
  'avg_cpv': ['cost', 'video_views'],
  'video_view_rate': ['video_views', 'impressions'],
  'interaction_rate': ['interactions', 'clicks'],
  'conversions_from_interactions_rate': ['conversions', 'interactions'],
  'cost_per_conversion': ['cost', 'conversions'],
  'cost_per_all_conversion': ['cost', 'all_conversions'],
  'all_conversion_rate': ['all_conversions', 'interactions'],
  'all_conversions_from_interactions_rate': [
    'all_conversions',
    'interactions',
  ],
}

DIMENSIONS = {
  'account_name': 'customer.descriptive_name',
  'campaign_name': 'campaign.name',
  'ad_group_name': 'ad_group.name',
}


class Period(pydantic.BaseModel):
  start_date: str | None = None
  end_date: str | None = None

  def validate_dates(self) -> None:
    """Checks whether provides start and end dates are valid.

    Args:
      start_date: Date in "YYYY-MM-DD" format.
      end_date: Date in "YYYY-MM-DD" format.

    Raises:
      ValueError:
        if start or end_date have incorrect format or start_date greater
        than end_date.
    """
    if not self.is_valid_date(self.start_date):
      raise ValueError(f'Invalid start_date: {self.start_date}')

    if not self.is_valid_date(self.end_date):
      raise ValueError(f'Invalid end_date: {self.end_date}')

    if datetime.datetime.strptime(
      self.start_date, '%Y-%m-%d'
    ) > datetime.datetime.strptime(self.end_date, '%Y-%m-%d'):
      raise ValueError(
        f'start_date cannot be greater than end_date: {self.start_date} > {self.end_date}'
      )

  def is_valid_date(self, date_string: str) -> bool:
    """Validates date.

    Args:
      date_string: Date to be validated.

    Returns:
      Whether or not the date is a string in "YYYY-MM-DD" format.

    Raises:
      ValueError: If string format is incorrect.
    """
    try:
      datetime.datetime.strptime(date_string, '%Y-%m-%d')
      return True
    except ValueError:
      return False

  def __bool__(self) -> bool:
    return bool(self.start_date and self.end_date)

  def __str__(self) -> str:
    return f"'{self.start_date}' AND '{self.end_date}'"


class BachQueryParameters(pydantic.BaseModel):
  resource: str
  metrics: Sequence[str] | None = None
  dimensions: Sequence[str] | None = None
  filters: Sequence[str] | None = None
  sorts: str | None = None
  period: Period = Period()
  limit: int | None = None


def _stringify(fields: Sequence[str]) -> str:
  return ', \n'.join(fields) if len(fields) > 1 else f'{fields[0]}'


class BachQuery(base_query.BaseQuery):
  """Interface for all queries."""

  query_template = """
  SELECT
    {dimensions},
    {metrics}
  FROM {resource}
  {filters}
  {sorts}
  {limit}
  """

  _TODAY = datetime.datetime.today()
  _START_DATE = _TODAY - datetime.timedelta(days=7)
  _END_DATE = _TODAY - datetime.timedelta(days=1)

  def __init__(self, parameters: BachQueryParameters | None = None) -> None:
    self.parameters = parameters
    self.default_dimensions = 'campaign.id AS campaign'

  @property
  def metrics(self) -> str:
    if metrics := self.parameters.metrics:
      return _stringify(metrics)
    return ''

  @property
  def limit(self) -> str:
    if limit := self.parameters.limit:
      return f'LIMIT {limit}'
    return ''

  @property
  def sorts(self) -> str:
    if sorts := self.parameters.sorts:
      return f'ORDER BY {sorts} DESC'
    return ''

  @property
  def filters(self) -> str:
    filter_str = ''
    dates_str = ''
    if dates := self.parameters.period:
      dates_str = f'segments.date BETWEEN {dates}'
    if filters := self.parameters.filters:
      filter_str = ' AND '.join(filters)
    if dates_str:
      return f'WHERE {dates_str} AND {filter_str}'
    if filter_str:
      return f'WHERE {filter_str}'
    return ''

  @property
  def dimensions(self) -> str:
    if dimensions := self.parameters.dimensions:
      return _stringify(dimensions)
    if self.parameters.limit:
      return self.default_dimensions + ',\n'
    return ''

  @property
  def query_text(self) -> str:
    expanded_query = self.query_template.format(
      metrics=self.metrics,
      dimensions=self.dimensions,
      filters=self.filters,
      limit=self.limit,
      sorts=self.sorts,
      resource=self.parameters.resource,
    )
    return ' '.join(expanded_query.replace('\n', '').split())

  def _build_query_part(self, spec) -> tuple[str, str] | None:
    """Returns metrics and corresponding filters based on a specification."""
    if spec.name in METRICS:
      value = (
        int(float(spec.value) * 1e6) if spec.name == 'cost' else spec.value
      )
      name = f'{spec.name}_micros' if spec.name == 'cost' else spec.name
      return (
        f'metrics.{name} {spec.operator} {value}',
        self._build_metric(spec.name),
      )
    return None

  def _build_metric(self, metric_name: str) -> str:
    name = (
      f'{metric_name}_micros / 1e6' if metric_name == 'cost' else metric_name
    )
    return f'metrics.{name} AS {metric_name}'

  def build(
    self,
    rule: str,
    limit: int | None = None,
  ):
    """Helper method for building query and fetching data from Ads API.

    Args:
      rule: Specification rule.
      limit: Whether to fetch all data or only a subset.

    Returns:
      Report containing placement performance data.
    """
    metrics: set[str] = set()
    filters: set[str] = set()
    dimensions: set[str] = set()
    if spec := exclusion_specification.ExclusionSpecification.from_expression(
      rule
    ):
      ads_specs = spec.ads_specs_entries.specifications
      for specs in ads_specs:
        for spec in specs:
          if compound_metrics := COMPOUND_METRICS.get(spec.name):
            for metric in compound_metrics:
              metrics.add(self._build_metric(metric))
          elif info := self._build_query_part(spec):
            ads_filter, ads_metric = info
            filters.add(ads_filter)
            metrics.add(ads_metric)
          elif dimension := DIMENSIONS.get(spec.name):
            dimensions.add(f'{dimension} AS {spec.name}')

    self.__init__(
      limit=limit,
      metrics=metrics,
      filters=filters,
      dimensions=dimensions,
    )
    return str(self)


DEFAULT_QUERIES: dict[str, str] = {
  'campaign_performance': """SELECT
          campaign.id AS campaign_id,
          metrics.clicks AS clicks
        FROM campaign
        DURING YESTERDAY
        """,
  'placement_performance': """
    SELECT
      customer.id AS customer_id,
      campaign.id AS campaign_id,
      campaign.advertising_channel_type AS campaign_type,
      ad_group.id AS ad_group_id,
      group_placement_view.placement_type AS placement_type,
      group_placement_view.placement AS placement,
      group_placement_view.display_name AS name,
      metrics.clicks AS clicks
    FROM group_placement_view
    WHERE group_placement_view.target_url NOT IN (
      'youtube.com',
      'mail.google.com',
      'adsenseformobileapps.com'
    )
    """,
  'keyword_performance': """
    SELECT
      customer.id AS customer_id,
      campaign.id AS campaign_id,
      ad_group.id AS ad_group_id,
      ad_group_criterion.keyword.text AS keyword,
      metrics.clicks AS clicks
    FROM keyword_view
    DURING YESTERDAY
    """,
  'search_term_performance': """
    SELECT
      customer.id AS customer_id,
      campaign.id AS campaign_id,
      ad_group.id AS ad_group_id,
      search_term_view.search_term AS search_term,
      metrics.clicks AS clicks
    FROM search_term_view
    DURING YESTERDAY
    """,
}
