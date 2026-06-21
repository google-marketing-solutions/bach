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

"""CLI entrypoint for running bach."""

import sys

import typer
from garf_executors.entrypoints import utils as garf_utils
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from typing_extensions import Annotated

import bach
from bach.entrypoints.tracer import (
  initialize_logger,
  initialize_tracer,
)
from bach.telemetry import tracer

LoggingInstrumentor().instrument(set_logging_format=False)
initialize_tracer()
initialize_logger()
typer_app = typer.Typer()


@typer_app.command()
@tracer.start_as_current_span('bach.cli.version')
def version() -> str:
  span = trace.get_current_span()
  span.set_attribute('version', bach.__version__)
  print(f'Bach version: {bach.__version__}')
  sys.exit()


@typer_app.command(
  context_settings={'allow_extra_args': True, 'ignore_unknown_options': True}
)
@tracer.start_as_current_span('bach.cli.run')
def run(
  ctx: typer.Context,
  area: Annotated[str, typer.Option(help='Type of Bach task to run')],
  rule: Annotated[str, typer.Option(help='Rule string')],
  accounts: Annotated[
    str, typer.Option(help='Comma-separated accounts to operate on')
  ],
  notify: Annotated[
    bool, typer.Option(help='Whether to send notifications')
  ] = False,
) -> str:
  span = trace.get_current_span()
  extra_parameters = garf_utils.ParamsParser(['area', 'notify']).parse(ctx.args)
  request = bach.BachRequest(
    rule=rule,
    accounts=accounts.split(','),
    area=area,
    area_parameters=extra_parameters.get('area'),
    notify=notify,
    notification_parameters=extra_parameters.get('notify'),
  )
  job = bach.Bach().play(request)
  print('Started operation %s', job.job_id)
