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

from __future__ import annotations

import os
from collections.abc import Sequence

import gaarf
from typing_extensions import Self

from bach import (
  actions,
  api_actors,
  exclusion_specification,
  notifications_channel,
  parsers,
  plugins,
  queries,
  report_fetcher,
  rules_parser,
  tasks,
)


class Bach:
  def __init__(self, repo) -> None:
    """Initializes Bach."""
    self.repo = repo
    self._rules = []
    self.type = ''
    self._query = ''
    self._matching_report = None
    self._accounts = []
    self._expand_mcc = False
    self._fetcher = None
    self._notification_channel = None

  def save_task(self, task) -> None:
    self.repo.add(task)

  def run_task(self, task: tasks.Task) -> None:
    (
      self.with_accounts(task.customer_ids)
      .with_type(task.type)
      .with_actor(
        plugins.PlacementExclusionActor,
        exclusion_level='CAMPAIGN',
      )
      .add_action(actions.Action.EXCLUDE)
      .add_rules(task.rule_expression)
      .fetch()
      .apply()
      .action()
      .notify()
    )

  def run(self) -> None:
    self.fetch().apply().action().notify()

  def with_fetcher(self, fetcher: report_fetcher.Fetcher) -> Self:
    self.fetcher = fetcher
    return self

  def with_actor(self, actor: api_actors.Actor, /, **kwargs: str) -> Self:
    client = gaarf.GoogleAdsApiClient(
      path_to_config=os.getenv('GOOGLE_ADS_YAML_PATH'),
    ).client
    self.actor = actor(client, **kwargs)
    return self

  def with_type(self, type: str = 'campaign_performance') -> Self:
    if query := queries.DEFAULT_QUERIES.get(type):
      self.type = type
      self._query = query
      return self
    raise ValueError('Unknown type of query: ', type)

  def with_accounts(
    self, *accounts: Sequence[int], expand_mcc: bool = False
  ) -> Self:
    self._accounts.extend(accounts)
    self._expand_mcc = expand_mcc
    return self

  def as_task(self, name: str, schedule: str | None = None) -> tasks.Task:
    return tasks.Task(
      name=name,
      type=self.type,
      rule_expression=''.join(self._rules),
      customer_ids=','.join(str(account) for account in self._accounts),
      date_range=0,
      from_days_ago=0,
      output=tasks.TaskOutput.NOTIFY,
      status=tasks.TaskStatus.ACTIVE,
      schedule=schedule,
    )

  def fetch(self, query: str | None = None, **kwargs: str) -> Self:
    if self._fetcher:
      return self._fetcher.fetch(self._accounts)
    self._report = gaarf.AdsReportFetcher(
      api_client=gaarf.GoogleAdsApiClient(
        path_to_config=os.getenv('GOOGLE_ADS_YAML_PATH')
      )
    ).fetch(
      query_specification=query or self._query,
      customer_ids=self._accounts,
      expand_mcc=self._expand_mcc,
    )
    return self

  def add_rules(self, *rules: Sequence[rules_parser.Rule | str]) -> Self:
    self._rules.extend(rules)
    self.spec = exclusion_specification.ExclusionSpecification.from_expression(
      ''.join(self._rules)
    )
    return self

  def apply_to(self, report: gaarf.report.GaarfReport) -> Self:
    if not self._rules:
      self._matching_report = report
    spec = exclusion_specification.ExclusionSpecification.from_expression(
      ''.join(self._rules)
    )
    self._matching_report = spec.apply_specifications(report)
    return self

  def apply(self) -> Self:
    if not self._rules:
      self._matching_report = self._report
      return self
    if ads_spec := self.spec.ads_specs_entries:
      matching_entries = ads_spec.apply_specifications(
        self._report, include_reason=False, include_matching_entity=False
      )
    else:
      matching_entries = None
    if non_ads_spec := self.spec.non_ads_specs_entries:
      parser = parsers.ExternalEntitiesParser()
      parser.parse_specification_chain(matching_entries, non_ads_spec)
    self._matching_report = self.spec.apply_specifications(matching_entries)
    return self

  def add_notify(
    self, notification_channel: notifications_channel.NotificationChannel
  ) -> Self:
    self._notification_channel = notification_channel
    return self

  def notify(
    self,
    notification_channel: notifications_channel.NotificationChannel
    | None = None,
  ) -> Self:
    if not notification_channel:
      notification_channel = self._notification_channel
    notification_channel.send(self._matching_report)
    return self

  def action(self) -> Self:
    self.actor.act(self._matching_report)
    return self

  def add_action(self, action: actions.Action = actions.Action.NOTIFY) -> None:
    self._action = action
    return self
