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

"""Performance placements exclusions from Google Ads."""

import datetime

from garf_core import report as garf_report

from bach.plugins.exclusions import base_excluder


class PlacementExclusionActor(base_excluder.BaseExclusionActor):
  """Responsible for excluding placements."""

  def _setup_criterion(
    self, entity_criterion, row: garf_report.GarfRow
  ) -> None:
    if row.placement_type == 'MOBILE_APPLICATION':
      entity_criterion.mobile_application.app_id = self._format_app_id(
        row.placement
      )
    if row.placement_type == 'WEBSITE':
      entity_criterion.placement.url = self._format_website(row.placement)
    if row.placement_type == 'YOUTUBE_VIDEO':
      entity_criterion.youtube_video.video_id = row.placement
    if row.placement_type == 'YOUTUBE_CHANNEL':
      entity_criterion.youtube_channel.channel_id = row.placement
    if self.exclusion_level != 'ACCOUNT':
      entity_criterion.negative = True

  def _format_app_id(self, app_id: str) -> str:
    """Returns app_id as acceptable negative criterion."""
    if app_id.startswith('mobileapp::'):
      criteria = app_id.split('-')
      app_id = criteria[-1]
      app_store = criteria[0].split('::')[-1]
      app_store = app_store.replace('mobileapp::1000', '')
      app_store = app_store.replace('1000', '')
      return f'{app_store}-{app_id}'
    return app_id

  def _format_website(self, website_url: str) -> str:
    """Returns website as acceptable negative criterion."""
    return website_url.split('/')[0]


class PlacementPerformance(base_excluder.ExcludableEntity):
  """Query for fetching placement performance."""

  name = 'placement_performance'

  _TODAY = datetime.datetime.today()
  _START_DATE = _TODAY - datetime.timedelta(days=7)
  _END_DATE = _TODAY - datetime.timedelta(days=1)
  _CAMPAIGN_TYPES = {'DISPLAY', 'VIDEO', 'SEARCH', 'DEMAND_GEN'}
  _PLACEMENT_TYPES = {
    'WEBSITE',
    'YOUTUBE_VIDEO',
    'YOUTUBE_CHANNEL',
    'MOBILE_APPLICATION',
    'MOBILE_APP_CATEGORY',
  }
  base_query_text = """
        SELECT
            customer.id AS customer_id,
            campaign.id AS campaign_id,
            campaign.advertising_channel_type AS campaign_type,
            ad_group.id AS ad_group_id,
            {extra_dimensions}
            {placement_level_granularity}.placement AS placement,
            {placement_level_granularity}.placement_type AS placement_type,
            {placement_level_granularity}.display_name AS name,
            {metrics}
        FROM {placement_level_granularity}
        WHERE segments.date >= "{start_date}"
            AND segments.date <= "{end_date}"
            AND {placement_level_granularity}.placement_type IN
                ("{placement_types}")
            AND {placement_level_granularity}.target_url NOT IN (
                "youtube.com", "mail.google.com", "adsenseformobileapps.com"
            )
            AND campaign.advertising_channel_type IN ("{campaign_types}")
            AND {filters}
        ORDER BY metrics.cost_micros DESC
        {limit}
        """

  def __init__(
    self,
    placement_types: tuple[str, ...] | None = None,
    campaign_types: tuple[str, ...] | None = None,
    placement_level_granularity: str = 'group_placement_view',
    start_date: str = _START_DATE.strftime('%Y-%m-%d'),
    end_date: str = _END_DATE.strftime('%Y-%m-%d'),
    metrics: dict[str, str] | None = None,
    filters: dict[str, str] | None = None,
    limit: int | None = 0,
  ):
    """Creates Garf query for fetching placements data.

    Args:
      placement_types: List of placement types that need to be fetched
        for exclusion.
      campaign_types: List of campaign types that need to be fetched.
      placement_level_granularity: API Resource to fetch data from.
      start_date: Start_date of the period.
      end_date: Start_date of the period.
      metrics: Metrics to be fetched.
      filters: Filters to be applied during fetching.
      limit: Number of rows to return in response.

    Raises:
      ValueError:
        If campaign_type, placement_type or placement_level_granularity
        are incorrect.
    """
    if campaign_types:
      if isinstance(campaign_types, str):
        campaign_types = tuple(campaign_types.split(','))
      if wrong_types := set(campaign_types).difference(self._CAMPAIGN_TYPES):
        raise ValueError('Wrong campaign type(s): ', ', '.join(wrong_types))
      self.campaign_types = '","'.join(campaign_types)
    else:
      self.campaign_types = '","'.join(self._CAMPAIGN_TYPES)
    if placement_types:
      if isinstance(placement_types, str):
        placement_types = tuple(placement_types.split(','))
      if wrong_types := set(placement_types).difference(self._PLACEMENT_TYPES):
        raise ValueError('Wrong placement(s): ', ', '.join(wrong_types))
      self.placement_types = '","'.join(placement_types)
    else:
      self.placement_types = '","'.join(self._PLACEMENT_TYPES)

    if placement_level_granularity not in (
      'detail_placement_view',
      'group_placement_view',
    ):
      raise ValueError(
        "Only 'detail_placement_view' or 'group_placement_view' "
        'can be specified!'
      )
    self.placement_level_granularity = placement_level_granularity

    self.validate_dates(start_date, end_date)
    self.start_date = start_date
    self.end_date = end_date
    self.parent_url = (
      'group_placement_target_url'
      if self.placement_level_granularity == 'detail_placement_view'
      else 'target_url'
    )
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
      'metrics.video_views AS video_views',
      'metrics.interactions AS interactions',
      'metrics.all_conversions AS all_conversions',
      'metrics.all_conversions_value AS all_conversions_value',
      'metrics.view_through_conversions AS view_through_conversions',
      'metrics.conversions_value AS conversions_value',
    }

  def _add_extra_dimensions(self) -> str:
    return f"""
            customer.descriptive_name AS account_name,
            campaign.name AS campaign_name,
            ad_group.name AS ad_group_name,
            {self.placement_level_granularity}.{self.parent_url} AS base_url,
            {self.placement_level_granularity}.target_url AS url,
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
