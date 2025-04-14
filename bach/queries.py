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

DEFAULT_QUERIES: dict[str, str] = {
  'campaign_performance': """SELECT
          campaign.id AS campaign_id,
          metrics.clicks AS clicks
        FROM campaign
        DURING YESTERDAY
        """,
  'placement_performance': """
    SELECT
      customer.id AS customer_id,
      campaign.id AS campaign_id,
      campaign.advertising_channel_type AS campaign_type,
      ad_group.id AS ad_group_id,
      group_placement_view.placement_type AS placement_type,
      group_placement_view.placement AS placement,
      group_placement_view.display_name AS name,
      metrics.clicks AS clicks
    FROM group_placement_view
    WHERE group_placement_view.target_url NOT IN (
      'youtube.com',
      'mail.google.com',
      'adsenseformobileapps.com'
    )
    """,
  'keyword_performance': """
    SELECT
      ad_group_criterion.keyword.text AS keyword,
      metrics.clicks AS clicks
    FROM keyword_view
    DURING YESTERDAY
    """,
  'search_term_performance': """
    SELECT
      customer.id AS customer_id,
      campaign.id AS campaign_id,
      ad_group.id AS ad_group_id,
      search_term_view.search_term AS search_term,
      metrics.clicks AS clicks
    FROM search_term_view
    DURING YESTERDAY
    """,
}
