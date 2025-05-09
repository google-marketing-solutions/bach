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

import datetime

from garf_core import report as garf_report

from bach.plugins.exclusions import base_excluder


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


_TODAY = datetime.datetime.today()
_START_DATE = _TODAY - datetime.timedelta(days=7)
_END_DATE = _TODAY - datetime.timedelta(days=1)


class BaseKeywordPerformanceQuery(base_excluder.ExcludableEntity):
  base_query_text = """
        SELECT
            customer.id AS customer_id,
            campaign.id AS campaign_id,
            ad_group.id AS ad_group_id,
            {entity},
            {extra_dimensions}
            {metrics}
        FROM {resource_name}
        WHERE segments.date >= "{start_date}"
            AND segments.date <= "{end_date}"
            AND {filters}
        ORDER BY metrics.cost_micros DESC
        {limit}
        """

  def __init__(
    self,
    resource_name: str,
    entity: str,
    start_date: str = _START_DATE.strftime('%Y-%m-%d'),
    end_date: str = _END_DATE.strftime('%Y-%m-%d'),
    metrics: dict[str, str] | None = None,
    filters: dict[str, str] | None = None,
    limit: int | None = 0,
  ):
    """Creates Garf query for fetching placements data.

    Args:
      start_date: Start_date of the period.
      end_date: Start_date of the period.
      metrics: Metrics to be fetched.
      filters: Filters to be applied during fetching.
      limit: Number of rows to return in response.
    """
    self.resource_name = resource_name
    self.entity = entity
    self.validate_dates(start_date, end_date)
    self.start_date = start_date
    self.end_date = end_date
    if not metrics:
      metrics = {
        'metrics.clicks AS clicks',
      }
    if limit and (limit := int(limit)):
      metrics.update(self._add_extra_metrics())
      self.extra_dimensions = self._add_extra_dimensions()
    else:
      self.extra_dimensions = ''
    metrics.add('metrics.cost_micros / 1e6 AS cost')

    self.metrics = ',\n'.join(metrics)
    if not filters:
      filters = {
        'metrics.clicks > 0',
        'metrics.impressions > 0',
        'metrics.cost_micros > 0',
      }
    self.filters = ' AND '.join(filters)
    self.limit = '' if not limit else f'LIMIT {limit}'
    self.query_text = self.base_query_text.format(**self.__dict__)

  def _add_extra_metrics(self) -> set[str]:
    return {
      'metrics.clicks AS clicks',
      'metrics.impressions AS impressions',
      'metrics.cost_micros / 1e6 AS cost',
      'metrics.conversions AS conversions',
      'metrics.all_conversions AS all_conversions',
      'metrics.all_conversions_value AS all_conversions_value',
      'metrics.conversions_value AS conversions_value',
    }

  def _add_extra_dimensions(self) -> str:
    return f"""
            customer.descriptive_name AS account_name,
            campaign.name AS campaign_name,
            ad_group.name AS ad_group_name,
            """

  def validate_dates(self, start_date: str, end_date: str) -> None:
    """Checks whether provides start and end dates are valid.

    Args:
      start_date: Date in "YYYY-MM-DD" format.
      end_date: Date in "YYYY-MM-DD" format.

    Raises:
      ValueError:
        if start or end_date have incorrect format or start_date greater
        than end_date.
    """
    if not self.is_valid_date(start_date):
      raise ValueError(f'Invalid start_date: {start_date}')

    if not self.is_valid_date(end_date):
      raise ValueError(f'Invalid end_date: {end_date}')

    if datetime.datetime.strptime(
      start_date, '%Y-%m-%d'
    ) > datetime.datetime.strptime(end_date, '%Y-%m-%d'):
      raise ValueError(
        f'start_date cannot be greater than end_date: {start_date} > {end_date}'
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


class KeywordPerformanceQuery(BaseKeywordPerformanceQuery):
  name = 'keyword_performance'

  def __init_(
    self,
    start_date: str = _START_DATE.strftime('%Y-%m-%d'),
    end_date: str = _END_DATE.strftime('%Y-%m-%d'),
    metrics: dict[str, str] | None = None,
    filters: dict[str, str] | None = None,
    limit: int | None = 0,
  ) -> None:
    super().__init_(
      'keyword_view',
      'ad_group_criterion.keyword.text AS keyword',
      start_date,
      end_date,
      metrics,
      filters,
      limit,
    )
