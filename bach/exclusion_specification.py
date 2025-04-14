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

"""Module for building and applying various specification.

ExclusionSpecification holds an expression is checked against a particular
GaarfRow object to verify whether or not this expression is true.
"""

from __future__ import annotations

import contextlib
import itertools
import logging
import math
import re
from collections.abc import Sequence

from gaarf import report

from bach import rules_parser


class BaseExclusionSpecificationEntry:
  """Base class for holding logic applicable to all specifications.

  Attributes:
    name:
      Name of the metric/dimension from Google Ads.
    operator:
      Comparator used to evaluate the expression.
    value:
      Expected value metric should take.
  """

  def __init__(self, expression: str, rule_type: str) -> None:
    """Constructor for the class.

    Args:
      expression: Exclusion expression in a form of `name > value`.
    """
    elements = [
      element.strip() for element in expression.split(' ', maxsplit=2)
    ]
    if len(elements) != 3:
      raise ValueError("Incorrect expression, specify in 'name > value' format")
    if elements[1] not in (
      '>',
      '>=',
      '<',
      '<=',
      '=',
      '!=',
      'regexp',
      'contains',
    ):
      raise ValueError(
        'Incorrect operator for expression, '
        "only '>', '>=', '<', '<=', '=', '!=', 'regexp', 'contains' ",
      )

    self.name = elements[0]
    self.operator = '==' if elements[1] == '=' else elements[1]
    self.__raw_value = elements[2].replace("'", '').replace('"', '')
    if self.__raw_value.lower() == 'true':
      self.value = True
    elif self.__raw_value.lower() == 'false':
      self.value = False
    else:
      self.value = self.__raw_value
    self.rule_type = rule_type

  def is_satisfied_by(self, entity_info: report.GaarfRow) -> tuple[bool, dict]:
    """Verifies whether given entity satisfies stored expression.

    Args:
      entity_info: GaarfRow object that contains entity data.

    Returns:
      Tuple with results of evaluation and all necessary information on
      entity (formatted as a dict).
    """
    if not hasattr(entity_info, self.name):
      raise ValueError(f'{entity_info} has no {self.name} attribute!')
    if hasattr(entity_info, 'is_processed') and not entity_info.is_processed:
      logging.debug(
        'Cannot get internal information on %s entity of type %s',
        entity_info.entity,
        entity_info.entity_type,
      )
      return False, {}
    if self.operator in ('regexp', 'contains'):
      return self._check_regexp(entity_info)
    return self._eval_expression(entity_info)

  def _check_regexp(self, entity: report.GaarfRow) -> bool:
    if entity_element := getattr(entity, self.name):
      return bool(
        re.search(
          rf'{self.value}',
          re.sub(r'[,.;@#?!&$]+', '', entity_element),
          re.IGNORECASE,
        )
      )
    return False

  def _eval_expression(self, entity: report.GaarfRow) -> bool:
    try:
      value = float(self.value)
    except ValueError:
      value = self.value
    if isinstance(value, float):
      return eval(
        f'{self._nan_to_zero(getattr(entity, self.name))}{self.operator} {value}'
      )
    return getattr(entity, self.name) == value

  def _nan_to_zero(self, value: str) -> float | str:
    return 0.0 if math.isnan(value) else value

  def __str__(self):
    return f'{self.rule_type}:{self.name} {self.operator} {self.value}'

  def __repr__(self):
    return (
      f'{self.__class__.__name__}'
      f"(rule_type='{self.rule_type}', "
      f"name='{self.name}', "
      f"operator='{self.operator}', value='{self.value}')"
    )

  def __eq__(self, other):
    return (self.rule_type, self.name, self.operator, self.value) == (
      other.rule_type,
      other.name,
      other.operator,
      other.value,
    )


class AdsExclusionSpecificationEntry(BaseExclusionSpecificationEntry):
  """Stores Google Ads specific rules."""

  def __init__(self, expression):
    super().__init__(expression, rule_type='GOOGLE_ADS_INFO')


class YouTubeChannelExclusionSpecificationEntry(
  BaseExclusionSpecificationEntry
):
  """Stores Google Ads specific rules."""

  def __init__(self, expression):
    super().__init__(expression, rule_type='YOUTUBE_CHANNEL_INFO')


AVAILABLE_SPECS_TYPES = {
  'GOOGLE_ADS_INFO': AdsExclusionSpecificationEntry,
  'YOUTUBE_CHANNEL_INFO': YouTubeChannelExclusionSpecificationEntry,
}


def create_exclusion_specification_entry(
  specification_type: str, condition: str
) -> BaseExclusionSpecificationEntry:
  """Builds concrete specification entry class based on type.

  Args:
    specification_type: Type of desired specification entry.
    condition: Expression to use for building the specification entry.

  Returns:
    Any subclass of instance of BaseExclusionSpecificationEntry.
  """
  if spec := AVAILABLE_SPECS_TYPES.get(specification_type):
    return spec(condition)
  raise ValueError(f'Incorrect type of rule: {specification_type}')


class ExclusionSpecification:
  """Verifies whether entities matches set of specification entries.

  Attributes:
    specifications: All specification entries within the specification.
  """

  def __init__(
    self,
    specifications: Sequence[Sequence[BaseExclusionSpecificationEntry]]
    | None = None,
  ) -> None:
    """Initializes ExclusionSpecification.

    Args:
      specifications: All specification entries within the specification.
    """
    self.specifications = specifications

  def apply_specifications(
    self,
    entities: report.GaarfReport,
    include_reason: bool = True,
    include_matching_entity: bool = True,
  ) -> report.GaarfReport:
    """Gets placements that satisfy exclusion specifications entries.

    Args:
      entities:
        Report to be checked against specifications.
      include_reason:
        Whether to include exclusion reason to output report.
      include_matching_entity:
        Whether to include matching entity to output report.

    Returns:
      Report filtered to entity that matches all
      specification entries.
    """
    if not self.specifications:
      return entities
    to_be_excluded_placements = []
    extra_columns: list[str] = []
    if include_reason:
      extra_columns.append('reason')
    if include_matching_entity:
      extra_columns.append('info')
    for entity in entities:
      reason = self.satisfies(entity)
      extra_data: list = []
      if reason:
        if include_reason:
          reason_str = ','.join(list(itertools.chain(*reason)))
          extra_data = [reason_str]
          if include_matching_entity:
            if hasattr(entity, 'extra_info'):
              extra_info = entity.extra_info.to_dict()
            else:
              extra_info = {}
            extra_data.append(extra_info)
        to_be_excluded_placements.append(entity.data + extra_data)
    desired_columns = entities.column_names + extra_columns
    with contextlib.suppress(ValueError):
      _ = desired_columns.pop(desired_columns.index('extra_info'))
    return report.GaarfReport(
      results=to_be_excluded_placements,
      column_names=entities.column_names + extra_columns,
    )[desired_columns]

  def satisfies(self, entity: report.GaarfRow) -> list[str]:
    """Verifies whether a single entity satisfies the specifications.

    Args:
      entity: GaarfRow object with placement data.

    Returns:
      Rules that entity satisfies.
    """
    rules_satisfied: list[str] = []
    for spec_entry in self.specifications:
      spec_satisfied: list[str] = []
      for spec in spec_entry:
        if spec.rule_type != 'GOOGLE_ADS_INFO':
          formatted_rule_type = spec.rule_type.replace('_INFO', '')
          if (
            formatted_rule_type != entity.placement_type
          ):  # TODO (amarkin): Fix to entity_type
            continue
          if not entity.extra_info:
            continue
          entity = entity.extra_info
        if spec.is_satisfied_by(entity):
          spec_satisfied.append(str(spec))
          continue
      if len(spec_satisfied) == len(spec_entry):
        rules_satisfied.append(spec_satisfied)
    return rules_satisfied

  @property
  def ads_specs_entries(self) -> ExclusionSpecification:
    """Specification filtered to Ads specific specification entries."""
    return self._get_specification_subset(
      include_rule_types={
        'GOOGLE_ADS_INFO',
      }
    )

  @property
  def non_ads_specs_entries(self) -> ExclusionSpecification:
    """Specification filtered to non-Ads specific specification entries."""
    return self._get_specification_subset(
      exclude_rule_types={
        'GOOGLE_ADS_INFO',
      }
    )

  def _get_specification_subset(
    self,
    include_rule_types: set[str] | None = None,
    exclude_rule_types: set[str] | None = None,
  ) -> ExclusionSpecification:
    """Builds new specification from a subset.

    Args:
      include_rule_types:
        Set of exclusion to include into new specifications.
      exclude_rule_types:
        Set of exclusion to include from new specifications.

    Returns:
      New ExclusionSpecification.
    """
    if not self.specifications:
      return ExclusionSpecification()
    specifications: list[list[BaseExclusionSpecificationEntry]] = []
    if include_rule_types:
      allowed_rule_types = include_rule_types
    else:
      exclude_rule_types = exclude_rule_types or set()
      allowed_rule_types = set(AVAILABLE_SPECS_TYPES.keys()).difference(
        exclude_rule_types
      )
    for specification in self.specifications:
      matching_specification = []
      for specification_entry in specification:
        if specification_entry.rule_type in allowed_rule_types:
          matching_specification.append(specification_entry)
      if matching_specification:
        specifications.append(matching_specification)
    return ExclusionSpecification(specifications=specifications)

  @classmethod
  def from_rules(
    cls, parsed_rules: list[list[rules_parser.Rule]] | None
  ) -> ExclusionSpecification:
    """Convert Exclusion rules into specifications."""
    if not parsed_rules:
      return ExclusionSpecification()
    specifications = []
    for rules in parsed_rules:
      specification_entry = []
      for rule in rules:
        specification_entry.append(
          create_exclusion_specification_entry(rule.type, rule.expression)
        )
      specifications.append(specification_entry)
    return ExclusionSpecification(specifications)

  @classmethod
  def from_expression(cls, rule_expression: str) -> ExclusionSpecification:
    """Convert raw string rules into specifications."""
    return ExclusionSpecification.from_rules(
      rules_parser.generate_rules(rule_expression)
    )

  def __eq__(self, other) -> bool:
    return self.specifications == other.specifications

  def __bool__(self) -> bool:
    return bool(self.specifications)
