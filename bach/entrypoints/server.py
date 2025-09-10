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


import pathlib

import fastapi
import typer
import uvicorn
from pydantic_settings import BaseSettings

import bach

typer_app = typer.Typer()


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


router = fastapi.APIRouter()


@router.post('/')
def play(
  request: bach.BachRequest,
) -> str:
  """Interacts with Bach."""
  bach.Bach().play(request)
  return 'success'


@typer_app.command()
def main(port: int = 8000):
  app = fastapi.FastAPI()
  app.include_router(router)
  uvicorn.run(app, port=port)


if __name__ == '__main__':
  main()
