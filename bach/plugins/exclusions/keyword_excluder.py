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
