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

import argparse

from bach import Bach


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('type', help='Help')
  parser.add_argument(
    '--accounts',
    nargs='+',
    dest='accounts',
    default='named_default_value',
    help='named_help',
  )
  parser.add_argument(
    '--expand',
    dest='expand',
    action='store_true',
    help='boolean_help',
  )
  args = parser.parse_args()

  bach = Bach()
  (
    bach.with_type(args.type)
    .with_accounts(*args.accounts, expand_mcc=True)
    .add_rules('clicks > 1')
    .fetch()
    .apply()
    .notify()
  )


if __name__ == '__main__':
  main()
