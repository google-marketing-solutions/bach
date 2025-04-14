# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Repository for storing SimilarityPairs."""

# pylint: disable=C0330, g-bad-import-order, g-multiple-import

import abc
import itertools
from collections.abc import MutableSequence, Sequence
from typing import Any, Final, Generic, Iterable, TypeVar

import sqlalchemy
from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import registry
from typing_extensions import override

from bach import tasks

DEFAULT_CHUNK_SIZE: Final[int] = 100
_T = TypeVar('_T')


def _batched(iterable: Iterable[Any], chunk_size: int):
  iterator = iter(iterable)
  while chunk := tuple(itertools.islice(iterator, chunk_size)):
    yield chunk


class BaseRepository(abc.ABC, Generic[_T]):
  """Interface for defining repositories."""

  def get(self, pairs: str | Sequence[str]) -> list[_T]:
    """Specifies get operations."""
    if isinstance(pairs, MutableSequence):
      pairs = {str(pair) for pair in pairs}
    else:
      pairs = (str(pairs),)
    if len(pairs) > DEFAULT_CHUNK_SIZE:
      results = [
        self._get(batch) for batch in _batched(pairs, DEFAULT_CHUNK_SIZE)
      ]
      return list(itertools.chain.from_iterable(results))
    return self._get(pairs)

  def add(
    self,
    pairs: _T | Sequence[_T],
  ) -> None:
    """Specifies add operations."""
    if not isinstance(pairs, MutableSequence):
      pairs = [pairs]
    self._add(pairs)

  @abc.abstractmethod
  def _get(self, pairs: str | Sequence[str]) -> list[_T]:
    """Specifies get operations."""

  @abc.abstractmethod
  def _add(
    self,
    pairs: _T | Sequence[_T],
  ) -> None:
    """Specifies get operations."""

  @abc.abstractmethod
  def list(self) -> list[_T]:
    """Returns all similarity pairs from the repository."""


class InMemoryRepository(BaseRepository, Generic[_T]):
  """Uses pickle files for persisting tagging results."""

  def __init__(self) -> None:
    """Initializes InMemoryRepository."""
    self.results = []

  @override
  def _get(self, pairs: str | Sequence[str]) -> list[_T]:
    return [result for result in self.results if result.key in pairs]

  @override
  def _add(
    self,
    pairs: _T | Sequence[_T],
  ) -> None:
    self.results.extend(pairs)

  @override
  def list(self) -> list[_T]:
    return self.results


mapper_registry = registry()

task_table = sqlalchemy.Table(
  'tasks',
  mapper_registry.metadata,
  Column('id', String(50), primary_key=True),
  Column('name', String(250)),
  Column('type', String(50)),
  Column('rule_expression', String(1000)),
  Column('customer_ids', String(1000)),
  Column('date_range', Integer),
  Column('from_days_ago', Integer),
  Column('output', Enum(tasks.TaskOutput)),
  Column('status', Enum(tasks.TaskStatus)),
  Column('creation_date', DateTime),
  Column('extra_info', JSON),
)
mapper_registry.map_imperatively(tasks.Task, task_table)


class SqlAlchemyRepository(BaseRepository):
  """Uses SqlAlchemy engine for persisting objects."""

  def __init__(self, db_url: str, model) -> None:
    """Initializes SqlAlchemyRepository."""
    self.db_url = db_url
    self.model = model

  def initialize(self) -> None:
    """Creates all ORM objects."""
    mapper_registry.metadata.create_all(self.engine)

  @property
  def session(self) -> sqlalchemy.orm.Session:
    """Property for initializing session."""
    return sqlalchemy.orm.sessionmaker(bind=self.engine)

  @property
  def engine(self) -> sqlalchemy.engine.Engine:
    """Initialized SQLalchemy engine."""
    return sqlalchemy.create_engine(self.db_url)

  @override
  def _get(self, pairs: str | Sequence[str]) -> list[_T]:
    with self.session() as session:
      return session.query(self.model).where(self.model.id.in_(pairs)).all()

  @override
  def _add(
    self,
    pairs: _T | Sequence[_T],
  ) -> None:
    with self.session() as session:
      for pair in pairs:
        session.add(pair)
      session.commit()

  def list(self) -> list[_T]:
    """Returns all tagging results from the repository."""
    with self.session() as session:
      return [res.to_model() for res in session.query(self.model).all()]
