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

import functools
from collections.abc import Sequence
from copy import deepcopy

from garf_core import report as garf_report

from bach import api_actors


class PlacementExclusionHandler(api_actors.OperationHandler):
  def __init__(self, client, exclusion_level: str) -> None:
    """Initializes PlacementExclusionHandler."""
    self.client = client
    self.exclusion_level = exclusion_level

  @functools.cached_property
  def mutate_operation(self):
    """Google Ads operation for changing negative criteria."""
    if self.exclusion_level == 'AD_GROUP':
      return self.client.get_service(
        'AdGroupCriterionService'
      ).mutate_ad_group_criteria
    if self.exclusion_level == 'CAMPAIGN':
      return self.client.get_service(
        'CampaignCriterionService'
      ).mutate_campaign_criteria
    if self.exclusion_level == 'ACCOUNT':
      return self.client.get_service(
        'CustomerNegativeCriterionService'
      ).mutate_customer_negative_criteria
    return None


class PlacementExclusionActor(api_actors.Actor):
  def __init__(
    self,
    client,
    exclusion_level: str,
    handlers: Sequence[type(api_actors.OperationHandler)] = (
      PlacementExclusionHandler,
    ),
  ) -> None:
    """Initializes PlacementExclusionActor."""
    super().__init__(handlers, exclusion_level=exclusion_level, client=client)
    self.client = client
    self.exclusion_level = exclusion_level

  @functools.cached_property
  def properties(self) -> dict:
    return {
      'AD_GROUP': {
        'criterion_operation': self.client.get_type(
          'AdGroupCriterionOperation'
        ),
        'criterion_service': self.client.get_service('AdGroupCriterionService'),
        'entity_id': 'ad_group_id',
      },
      'CAMPAIGN': {
        'criterion_operation': self.client.get_type(
          'CampaignCriterionOperation'
        ),
        'criterion_service': self.client.get_service(
          'CampaignCriterionService'
        ),
        'entity_id': 'campaign_id',
      },
      'ACCOUNT': {
        'criterion_operation': self.client.get_type(
          'CustomerNegativeCriterionOperation'
        ),
        'criterion_service': self.client.get_service(
          'CustomerNegativeCriterionService'
        ),
        'entity_id': 'campaign_id',
      },
    }

  def _create_placement_operation(
    self,
    placement_info: garf_report.GarfRow,
    placement_exclusion_lists: dict[str, str],
  ) -> tuple[api_actors.OperationHandler, api_actors.MutateOperation]:
    """Create exclusion operation for a single placement."""
    # if (
    #   self.exclusion_level in ('CAMPAIGN', 'AD_GROUP')
    #   and placement_info.campaign_type in self.associable_with_negative_lists
    # ):
    #   return self._create_campaign_set_operation(placement_info)
    entity_criterion = (
      self.properties.get(self.exclusion_level)
      .get('criterion_operation')
      .create
    )
    if placement_info.placement_type == 'MOBILE_APPLICATION':
      app_id = self._format_app_id(placement_info.placement)
    if placement_info.placement_type == 'WEBSITE':
      entity_criterion.placement.url = self._format_website(
        placement_info.placement
      )
    if placement_info.placement_type == 'MOBILE_APPLICATION':
      entity_criterion.mobile_application.app_id = app_id
    if placement_info.placement_type == 'YOUTUBE_VIDEO':
      entity_criterion.youtube_video.video_id = placement_info.placement
    if placement_info.placement_type == 'YOUTUBE_CHANNEL':
      entity_criterion.youtube_channel.channel_id = placement_info.placement
    if self.exclusion_level != 'ACCOUNT':
      entity_criterion.negative = True
    if self.exclusion_level == 'AD_GROUP':
      entity_criterion.ad_group = (
        self.properties.get(self.exclusion_level)
        .get('criterion_service')
        .ad_group_path(
          placement_info.customer_id,
          placement_info.get(
            self.properties.get(self.exclusion_level).get('entity_id')
          ),
        )
      )
    elif self.exclusion_level == 'CAMPAIGN':
      entity_criterion.campaign = (
        self.properties.get(self.exclusion_level)
        .get('criterion_service')
        .campaign_path(
          placement_info.customer_id,
          placement_info.get(
            self.properties.get(self.exclusion_level).get('entity_id')
          ),
        )
      )
    operation = deepcopy(
      self.properties.get(self.exclusion_level).get('criterion_operation')
    )
    return (
      PlacementExclusionHandler,
      api_actors.MutateOperation(
        customer_id=placement_info.customer_id,
        operation=operation,
      ),
    )

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
