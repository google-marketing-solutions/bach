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

# pylint: disable=C0330, g-bad-import-order, g-multiple-imporf

from collections.abc import Sequence
from typing import Callable, Final

import garf_core
import garf_youtube_data_api

VIDEOS_QUERY: Final[str] = """
SELECT
  id,
  snippet.title AS title,
  snippet.description AS description,
  snippet.defaultLanguage AS defaultLanguage,
  snippet.defaultAudioLanguage AS defaultAudioLanguage,
  statistics.commentCount AS commentCount,
  statistics.favouriteCount AS favouriteCount,
  statistics.likeCount AS likeCount,
  statistics.viewCount AS viewCount,
  status.madeForKids AS madeForKids,
  snippet.tags AS tags,
  topicDetails.topicCategories AS topicCategories
FROM channels
"""


def get_video_info(
  placements: Sequence[str], **kwargs: str
) -> dict[str, garf_core.report.GarfRow]:
  entities = []
  for row in placements:
    for key, value in kwargs.items():
      if row[key] == value:
        entities.append(row.placement)
  if not entities:
    return {}
  results = garf_youtube_data_api.YouTubeDataApiReportFetcher(
    garf_youtube_data_api.YouTubeDataApiClient()
  ).fetch(VIDEOS_QUERY, id=placements)
  output = {}
  for row in results:
    output[row.id] = row
  return output


CHANNELS_QUERY: Final[str] = """
SELECT
  id,
  snippet.title AS title,
  snippet.description AS description,
  snippet.defaultLanguage AS defaultLanguage,
  snippet.defaultAudioLanguage AS defaultAudioLanguage,
  statistics.commentCount AS commentCount,
  statistics.favouriteCount AS favouriteCount,
  statistics.likeCount AS likeCount,
  statistics.viewCount AS viewCount,
  status.madeForKids AS madeForKids,
  snippet.tags AS tags,
  topicDetails.topicCategories AS topicCategories
FROM channels
"""


def get_channel_info(
  placements: Sequence[str], **kwargs: str
) -> dict[str, garf_core.report.GarfRow]:
  entities = []
  for row in placements:
    for key, value in kwargs.items():
      if row[key] == value:
        entities.append(row.placement)
  if not entities:
    return {}
  results = garf_youtube_data_api.YouTubeDataApiReportFetcher(
    garf_youtube_data_api.YouTubeDataApiClient()
  ).fetch(CHANNELS_QUERY, id=entities)
  output = {}
  for row in results:
    output[row.id] = row
  return output


PARSER_MAPPING: dict[str, Callable] = {
  'YOUTUBE_CHANNEL_INFO': get_channel_info,
  'YOUTUBE_VIDEO_INFO': get_video_info,
}
