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

"""Discovers available Bach plugins."""

import inspect
from importlib.metadata import entry_points

from bach import api_actors, exceptions


def load_actor(actor_name: str) -> type[api_actors.Actor]:
  """Locates actor with a specified name.

  Args:
    actor_name: Name of an actor to load.

  Returns:
    Actor class.

  Raises:
    BachError: If actor not found or cannot be loaded.
  """
  actors = entry_points(group='bach_actors')
  for actor in actors:
    if actor.name != actor_name:
      continue
    try:
      actor_module = actor.load()
      for name, obj in inspect.getmembers(actor_module):
        if inspect.isclass(obj) and issubclass(obj, api_actors.Actor):
          return getattr(actor_module, name)
    except ModuleNotFoundError as e:
      raise exceptions.BachError(f'Failed to import actor {actor_name}') from e
  available_actors = ', '.join(sorted(actor.name for actor in actors))
  raise exceptions.BachError(
    f'Unsupported actor <{actor_name}>, '
    f'select one of available: {available_actors}'
  )


def list_actors() -> list[str]:
  """Finds all available Bach actors."""
  return [actor.name for actor in entry_points(group='bach_actors')]
