# Copyright 2023 Google LLC
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

"""Module for translating exclusion rule into specifications."""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Sequence


@dataclasses.dataclass(frozen=True)
class Rule:
  """Holds information on a rule."""

  type: str
  expression: str


def generate_rules(raw_rules: str | Sequence[str]) -> list[list[Rule]] | None:
  """Convert raw string rules into a list of Rules.

  Rule as raw string can be expressed in an explicit
  (`rule_type:exclusion_rule`), implicit (`exclusion_rule`) format.

  Rules in each of these formats can be represented as sequence or a single
  string. And-rules are separated by `AND` keyword or comma (`,`),
  Or-rules are separated by `OR` keyword.

  If `rule_type` is not specified for a given rule it's treated
  as GOOGLE_ADS_INFO.
  """
  rules: list[list[Rule]] = []
  if not raw_rules:
    return rules
  default_rule_type = 'GOOGLE_ADS_INFO'
  if isinstance(raw_rules, str):
    raw_rules = _format_raw_rules(raw_rules)
  for rule in raw_rules:
    current_rule_type = None
    types = rule.split(',') if ',' in rule else rule.split(' AND ')
    rule_entry: list[Rule] = []
    for type_ in types:
      spec_ = type_.split(':')
      if len(spec_) == 1:
        if not current_rule_type:
          rule_type = default_rule_type
        else:
          rule_type = str(current_rule_type)
        expression_position = 0
      else:
        rule_type = spec_[0]
        expression_position = 1
      current_rule_type = str(rule_type)
      rule_expression = spec_[expression_position].rstrip()
      rule_entry.append(
        Rule(
          type=rule_type.strip(),
          expression=_convert_rule_expression(rule_expression.strip()),
        )
      )
    rules.append(rule_entry)
  return rules


def _format_raw_rules(raw_rules: str) -> list[str]:
  """Applies formatting to raw string rule."""
  # Removes brackets.
  raw_rules = re.sub('[(|)]', '', raw_rules)
  # Adds whitespace in front of operators.
  raw_rules = re.sub('([>|<|>=|<=|!=|=])', r' \1 ', raw_rules)
  # Trims extra whitespace.
  raw_rules = re.sub(' +', ' ', raw_rules)
  # Split rules by OR operator.
  return raw_rules.split(' OR ')


def _convert_rule_expression(rule_expression: str) -> str:
  """Handles conversion of composite rule into atomic one."""
  if 'letter_set' in rule_expression:
    return rule_expression.replace(
      'letter_set latin_only',
      "regexp '^[a-zA-Z0-9\s\W]*$'",
    ).replace('letter_set no_latin', "regexp '^[^a-zA-Z]*$'")
  return rule_expression
