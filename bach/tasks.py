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

import dataclasses
import datetime
import enum
import math
import uuid
from typing import Any, Final

from croniter import croniter

_HOURS_IN_DAY: Final[int] = 24


class TaskStatus(enum.Enum):
  """An enumeration representing the status of a task."""

  ACTIVE = 0
  INACTIVE = 1


class TaskOutput(enum.Enum):
  """An enumeration representing the artifact/output options for a task."""

  NOTIFY = 1
  APPLY = 2


@dataclasses.dataclass
class Task:
  """Defines task that needs to be run by an application.

  Task contains all necessary information to find the appropriate entities.

  Attributes:
    name: Task name.
    rule_expression: String version of exclusion rule.
    date_range: Lookback days for data fetching from Google Ads API.
    from_days_ago: start_date of data fetching from Google Ads API.
    outputs: Desired action (APPLY, NOTIFY, etc.)
    status: Task status.
    schedule: Optional task schedule.
    creation_date: Time when task was created.
    id: Unique task identifier.
  """

  name: str
  type: str
  rule_expression: str
  customer_ids: str
  date_range: int = 7
  from_days_ago: int = 0
  output: TaskOutput = TaskOutput.NOTIFY
  status: TaskStatus = TaskStatus.ACTIVE
  schedule: str | None = None
  creation_date: datetime.datetime = datetime.datetime.now()
  extra_info: dict[str, Any] = dataclasses.field(default_factory=dict)
  id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

  def __post_init__(self) -> None:
    """Ensures safe casting to proper enums."""
    self.output = self._cast_to_enum(TaskOutput, self.output)
    self.status = self._cast_to_enum(TaskStatus, self.status)

  def to_dict(self) -> dict[str, int | str]:
    """Converts class to dictionary.

    Enum attributes of the class are represented as names.
    """
    task_dict = {}
    for key, value in dataclasses.asdict(self).items():
      if hasattr(value, 'value'):
        task_dict[key] = value.name
      else:
        task_dict[key] = value
    return task_dict

  @property
  def cron_schedule(self) -> str | None:
    """Builds cron schedule based on creation time and schedule."""
    minute = self.creation_date.strftime('%M')
    hour = self.creation_date.strftime('%H')

    if not (schedule := self.schedule) or self.schedule == '0':
      return None
    if 0 < int(schedule) < _HOURS_IN_DAY:
      schedule = f'{minute} */{schedule} * * *'
    elif int(schedule) >= _HOURS_IN_DAY:
      days = math.floor(int(self.schedule) / _HOURS_IN_DAY)
      schedule = f'{minute} {hour} */{days} * *'
    return schedule

  @property
  def start_date(self) -> str:
    """Formatted start_date."""
    return (
      (
        datetime.datetime.now()
        - datetime.timedelta(days=int(self.from_days_ago + self.date_range))
      )
      .date()
      .strftime('%Y-%m-%d')
    )

  @property
  def end_date(self) -> str:
    """Formatted end_date."""
    return (
      (
        datetime.datetime.now()
        - datetime.timedelta(days=int(self.from_days_ago))
      )
      .date()
      .strftime('%Y-%m-%d')
    )

  @property
  def accounts(self) -> list[str]:
    """Formatted account list."""
    return (
      self.customer_ids.split(',')
      if isinstance(self.customer_ids, str)
      else self.customer_ids
    )

  @property
  def next_run(self) -> str:
    """Next task run as a cron expression."""
    if not (schedule := self.cron_schedule):
      return 'Not scheduled'
    return (
      croniter(schedule, datetime.datetime.now())
      .get_next(datetime.datetime)
      .strftime('%Y-%m-%d %H:%M')
    )

  def _cast_to_enum(
    self, enum_: type[enum.Enum], value: str | enum.Enum
  ) -> enum.Enum:
    """Helper method for converted in string to desired enum.

    Args:
      enum_: Enum class to server as conversion base.
      value: Value to perform the conversion.

    Returns:
      Correct enum based on provided value.
    """
    return enum_[value] if isinstance(value, str) else value


class ExecutionTypeEnum(enum.Enum):
  """Holds type of Task execution."""

  SCHEDULED = 0
  MANUAL = 1


@dataclasses.dataclass
class Execution:
  """Holds information of a particular task run.

  Attributes:
    task: Id of a task.
    start_date: Time when execution started.
    end_date: Time when execution ended.
    entities_modified: Number of excluded placements.
    type: Type of execution (MANUAL, SCHEDULED).
    id: Unique identifier of execution.
  """

  task: int
  start_time: datetime.datetime
  end_time: datetime.datetime
  entities_modified: int
  type: ExecutionTypeEnum
  id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))

  def __post_init__(self) -> None:
    """Ensures that strings are always cast to proper enum."""
    self.type = self._cast_to_enum(ExecutionTypeEnum, self.type)

  def _cast_to_enum(
    self, enum_: type[enum.Enum], value: str | enum.Enum
  ) -> enum.Enum:
    """Cast to proper enum."""
    return enum_[value] if isinstance(value, str) else value


@dataclasses.dataclass
class ExecutionDetails:
  """Holds detailed information on a particular execution.

  Attributes:
    execution_id: Unique identifier of an execution.
    entity: Entity identifier that was modified during the execution.
    entity_type: Type of modified entity.
    reason: Reason for modification.
    id: Unique identifier of execution details entry.
  """

  execution_id: str
  entity: str
  entity_type: str
  reason: str
  id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
