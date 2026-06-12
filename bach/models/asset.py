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
import datetime

import pydantic
from google.ads.googleads.client import GoogleAdsClient
from typing_extensions import override


class Asset(pydantic.BaseModel):
  """Base class for Asset."""

  url: pydantic.HttpUrl = pydantic.Field(exclude=True)

  def to_operation(self, client: GoogleAdsClient):
    """Converts models to a corresponding mutate operation."""
    raise NotImplementedError


class Text(Asset):
  text: str


class Sitelink(Asset):
  link_text: str = pydantic.Field(min_length=1, max_length=25)
  description1: str | None = pydantic.Field(
    default=None, min_length=1, max_length=35
  )
  description2: str | None = pydantic.Field(
    default=None, min_length=1, max_length=35
  )
  start_date: datetime.date | None = None
  end_date: datetime.date | None = None

  def model_post_init(self, __context):
    if (self.description2 and not self.description1) or (
      self.description1 and not self.description2
    ):
      raise SitelinkError('Set both description lines')

  @override
  def to_operation(self, client):
    asset_operation = client.get_type('AssetOperation')
    asset = asset_operation.create
    asset.final_urls.append(str(self.url))
    if self.description1:
      asset.sitelink_asset.description1 = self.description1
    if self.description2:
      asset.sitelink_asset.description2 = self.description2
    asset.sitelink_asset.link_text = self.link_text
    return asset_operation
