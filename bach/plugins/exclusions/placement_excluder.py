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
