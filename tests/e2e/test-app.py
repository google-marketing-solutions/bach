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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import, missing-class-docstring, missing-module-docstring, missing-function-docstring
import pathlib

import garf.core
import pydantic
from garf.executors.workflows import Workflow, WorkflowRunner

from bach import (
  exclusion_specification,
  notifications_channel,
)

_SCRIPT_PATH = pathlib.Path(__file__).parent


class BachWorkflowError(Exception):
  """Bach workflow specific exception."""


class BachWorkflow(Workflow):
  def model_post_init(self, __context):
    last_step = self.steps[-1]
    if alias := (last_step.alias) != 'task':
      raise BachWorkflowError(f'Final step should be task, got {alias}')
    if (n_queries := len(last_step.queries)) > 1:
      raise BachWorkflowError(
        f'Expected a single query as a task, got {n_queries} instead'
      )

  @pydantic.computed_field
  @property
  def identifier(self) -> str:
    return self.steps[-1].queries[0].title


bach_workflow = BachWorkflow.from_file(_SCRIPT_PATH / 'bach_workflow.yaml')


class BachRequest(pydantic.BaseModel):
  workflow: BachWorkflow
  rule: str
  # actor: Actor | None = None

  def fetch(self):
    results = WorkflowRunner(self.workflow).run()
    return list(results.values())[0].get(self.workflow.identifier)

  def notify(
    self,
    report: garf.core.GarfReport,
    notification_channel: notifications_channel.NotificationChannel,
  ):
    notification_channel.send(report)

  def play(self):
    report = self.apply()
    self.notify(report, notification_channel=notifications_channel.Console())

  def apply(self):
    report = self.fetch()
    spec = exclusion_specification.ExclusionSpecification.from_expression(
      self.rule
    )
    return spec.apply_specifications(report)


request = BachRequest(
  workflow=bach_workflow,
  rule='value > 50',
)
result = request.play()
