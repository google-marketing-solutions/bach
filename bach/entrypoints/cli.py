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

import argparse
import sys

from garf_executors.entrypoints import utils as garf_utils

import bach


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--area', help='Type of Bach task to run')
  parser.add_argument(
    '--accounts',
    nargs='+',
    dest='accounts',
    default=None,
    help='Accounts to operate on',
  )
  parser.add_argument('--rule', default=None, help='Rule string')
  parser.add_argument(
    '--notify',
    default=None,
    help='Where to send notifications',
  )
  parser.add_argument(
    '--version',
    '-v',
    dest='version',
    action='store_true',
    help='Version of bach CLI utility',
  )
  args, kwargs = parser.parse_known_args()

  if args.version:
    print(f'Bach version: {bach.__version__}')
    sys.exit()

  extra_parameters = garf_utils.ParamsParser(['area', 'notify']).parse(kwargs)
  request = bach.BachRequest(
    rules=args.rule,
    accounts=args.accounts,
    area=args.area,
    area_parameters=extra_parameters.get('area'),
    notification_parameters=extra_parameters.get('notify'),
  )
  bach.Bach().play(request)


if __name__ == '__main__':
  main()
