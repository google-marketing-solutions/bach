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

import os

import dotenv
import fastapi
from fastapi import testclient

import bach
from bach.entrypoints import server

client = testclient.TestClient(server.app)

dotenv.load_dotenv()


class TestBach:
  def test_play(self):
    request = bach.BachRequest(
      area='placement_performance',
      rule='clicks > 100',
      accounts=[os.getenv('EEM_MCC')],
    )
    response = client.post('/', json=request.model_dump())
    assert response.status_code == fastapi.status.HTTP_200_OK
