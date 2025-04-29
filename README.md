# bach for Google Ads

`bach` provides an easy to use set of abstractions to simplify
developing Google Ads solutions related to Google Ads management.
Most of the solutions consist of three phases:

* Extract some data
* Do some transformation
* Do something with transformed data

`bach` solves first two generically by simplifying fetching data and applying filtering rules to the fetched data;
the third step is defined as an interface developers can use to build on top of it.

Responsible for orchestrating rules and applying complex rules in Google Ads.
Consists of 3 elements:

* **Rule to Query** - takes complex rules and build GAQL query out of it; query is executed and returned as a `Report`.
* **Rule to Report** - applies Rule to Report to get a subset of actionable entities.
* **Report to Action** - does whatever needs to be done with the subset of data (notification, exclusion, increase / decrease).

## Installation

`pip install bach-googleads`


## Usage

1. Simple use case - use predefined queries.

```
from bach import (
  Bach,
  actions,
  notifications_channel,
  plugins,
)
from bach.adapters import repositories

task_repo = repositories.SqlAlchemyRepository(
  db_url='sqlite:///tasks.db', model=tasks.Task
)

bach = Bach(task_repo)

(
  bach
  .with_type('placement_performance')
  .with_accounts(ACCOUNT_ID)
  .with_actor(
    plugins.PlacementExclusionActor,
    exclusion_level='CAMPAIGN',
  )
  .add_rules('clicks > 10')
  .add_action(actions.Action.EXCLUDE)
  .add_notify(notifications_channel.Console())
)

bach.run()
bach_task = bach.as_task(name='task_name')
```


2. Simple use case - use custom query.

```
from bach import Bach

query = 'SELECT campaign.id, metrics.clicks AS clicks FROM campaign'

(
  bach
  .with_accounts(ACCOUNT_ID)
  .add_rules('clicks > 0')
  .fetch(query)
  .apply()
  .notify()
)
```

3. Advanced use case - use custom fetcher.

```
from bach import Bach

from bach.fetchers import placement_fetcher

(
  bach
  .with_fetcher(placement_fetcher.PlacementFetcher())
  .with_accounts(ACCOUNT_ID)
  .add_rules('clicks > 0')
  .fetch()
  .apply()
  .notify()
)
```

4. Running a task.

```
from bach import Bach, tasks


task = tasks.Task(
  name='test_task',
  type='campaign_performance',
  customer_ids=ACCOUNT_ID,
  rule_expression='clicks > 1',
  extra_info={'campaign_type': 'DISPLAY'},
)

bach.run_task(task)
```
