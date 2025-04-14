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

# pylint: disable=C0330, g-bad-import-order, g-multiple-import import abc import collections

import abc
import collections
import dataclasses
import logging
from collections.abc import Sequence

import tenacity
from garf_core import report as garf_report
from google.api_core import exceptions as google_api_exceptions


@dataclasses.dataclass
class MutateOperation:
  """Base class for all mutate operations."""

  customer_id: int
  operation: str


@dataclasses.dataclass
class MutateOperationResult:
  entities_mutated: int


class OperationHandler(abc.ABC):
  def handle(
    self, customer_id: int, operations: Sequence[MutateOperation]
  ) -> MutateOperationResult:
    """Defines mutate operations for a given customer_id."""
    if not isinstance(operations, Sequence):
      operations = [operations]
    try:
      for attempt in tenacity.Retrying(
        retry=tenacity.retry_if_exception_type(
          google_api_exceptions.InternalServerError
        ),
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(),
      ):
        with attempt:
          operations = [operation.operation for operation in operations]
          self.mutate_operation(
            customer_id=str(customer_id),
            operations=operations,
          )
          return MutateOperationResult(entities_mutated=len(operations))
    except tenacity.RetryError as retry_failure:
      logging.error(
        "Cannot execute mutate operations for account '%s' %d times",
        customer_id,
        retry_failure.last_attempt.attempt_number,
      )

    @abc.abstractproperty
    def mutate_operation(self):
      """Specifies how to perform mutate."""


class Actor(abc.ABC):
  def __init__(
    self, handlers: Sequence[type(OperationHandler)], **kwargs: str
  ) -> None:
    """Initializes Actor."""
    self.handlers = {handler: handler(**kwargs) for handler in handlers}

  def act(self, report: garf_report.GarfReport, **kwargs: str) -> None:
    """Defines action that needs to be performed on report."""
    for handler, mutate_operations in self._prepare_mutate_operations(
      report, **kwargs
    ).items():
      for customer_id, operations in mutate_operations.items():
        try:
          if operations:
            initialized_handler = self.handlers.get(handler)
            logging.info(initialized_handler.handle(customer_id, operations))
        except Exception as e:
          logging.error(e)

  def _prepare_mutate_operations(
    self,
    report: garf_report.GarfReport,
    placement_exclusion_lists: dict[str, str] | None = None,
  ) -> dict[OperationHandler, dict[int, Sequence[MutateOperation]]]:
    """Defines mapping between customer_id and its mutate operations."""
    handler_operations: dict = collections.defaultdict(
      lambda: collections.defaultdict(list)
    )
    for row in report:
      handler, operation = self._create_placement_operation(
        row, placement_exclusion_lists
      )
      handler_operations[handler][row.customer_id].append(operation)
    return handler_operations

  @abc.abstractmethod
  def _create_placement_operation(
    self, row: garf_report.GarfRow, **kwargs: str
  ) -> tuple[OperationHandler, MutateOperation]:
    """Create mutate operation for a single entity."""
