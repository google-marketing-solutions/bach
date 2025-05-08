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

"""Common functionality for all exclusion plugins."""

import functools
from collections.abc import Sequence
from copy import deepcopy

from garf_core import report as garf_report

from bach import api_actors


class BaseExclusionHandler(api_actors.OperationHandler):
  """Specifies common mutate operations for exclusions."""

  def __init__(self, client, exclusion_level: str) -> None:
    """Initializes BaseExclusionHandler."""
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


class BaseExclusionActor(api_actors.Actor):
  """Specifies common functionality of performing exclusions from Google Ads.

  Concrete excluders should inherit from this class and overwrite
  `_setup_criterion` method.
  """

  def __init__(
    self,
    client,
    exclusion_level: str,
    handlers: Sequence[type(api_actors.OperationHandler)] = (
      BaseExclusionHandler,
    ),
  ) -> None:
    """Initializes BaseExclusionActor."""
    super().__init__(handlers, exclusion_level=exclusion_level, client=client)
    self.client = client
    self.exclusion_level = exclusion_level

  @functools.cached_property
  def properties(self):
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

  def _setup_criterion(
    self, entity_criterion, row: garf_report.GarfRow
  ) -> None:
    raise NotImplementedError

  def _create_mutate_operation(
    self, row: garf_report.GarfRow, **kwargs: str
  ) -> tuple[api_actors.OperationHandler, api_actors.MutateOperation]:
    """Create exclusion operation for a single placement."""
    entity_criterion = (
      self.properties.get(self.exclusion_level)
      .get('criterion_operation')
      .create
    )
    self._setup_criterion(entity_criterion, row)
    if self.exclusion_level == 'AD_GROUP':
      entity_criterion.ad_group = (
        self.properties.get(self.exclusion_level)
        .get('criterion_service')
        .ad_group_path(
          row.customer_id,
          row.get(self.properties.get(self.exclusion_level).get('entity_id')),
        )
      )
    elif self.exclusion_level == 'CAMPAIGN':
      entity_criterion.campaign = (
        self.properties.get(self.exclusion_level)
        .get('criterion_service')
        .campaign_path(
          row.customer_id,
          row.get(self.properties.get(self.exclusion_level).get('entity_id')),
        )
      )
    operation = deepcopy(
      self.properties.get(self.exclusion_level).get('criterion_operation')
    )
    return (
      BaseExclusionHandler,
      api_actors.MutateOperation(
        customer_id=row.customer_id, operation=operation
      ),
    )
