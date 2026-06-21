# Copyright 2026 Google LLC
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


import pathlib

import fastapi
import typer
import uvicorn
from garf.executors.entrypoints import utils as garf_utils
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from pydantic_settings import BaseSettings
from typing_extensions import Annotated

import bach
from bach import telemetry
from bach.entrypoints.tracer import (
  initialize_logger,
  initialize_meter,
  initialize_tracer,
)

typer_app = typer.Typer()
OTEL_SERVICE_NAME = 'bach'
LoggingInstrumentor().instrument(set_logging_format=False)

initialize_tracer()
meter = initialize_meter()

logger = garf_utils.init_logging(
  loglevel='INFO', logger_type='local', name=OTEL_SERVICE_NAME
)
logger.addHandler(initialize_logger())

CeleryInstrumentor().instrument()
RedisInstrumentor().instrument()
app = fastapi.FastAPI(
  title='Bach',
  version=bach.__version__,
  description='Manage tasks in Google Ads',
)
FastAPIInstrumentor.instrument_app(app)


class BachServerSettings(BaseSettings):
  """Specifies environmental variables for Bach.

  Ensure that mandatory variables are exposed via
  export ENV_VARIABLE_NAME=VALUE.

  Attributes:
    google_ads_configuration_file_path: Path to google-ads.yaml.
  """

  google_ads_configuration_file_path: str = str(
    pathlib.Path.home() / 'google-ads.yaml'
  )


@app.get('/api/version')
def version():
  return bach.__version__


@app.post('/api/')
def play(
  request: bach.BachRequest,
) -> str:
  """Interacts with Bach."""
  bach.Bach().play(request)
  return 'success'


def main(
  host: Annotated[
    str, typer.Option(help='Host to start the server')
  ] = '0.0.0.0',
  port: Annotated[
    int, typer.Option('--port', '-p', help='Port to start the server')
  ] = 8000,
):
  telemetry.bach_info.set(
    1,
    {
      'version': bach.__version__,
    },
  )
  uvicorn.run(app, host=host, port=port, log_config=None)


if __name__ == '__main__':
  main()
