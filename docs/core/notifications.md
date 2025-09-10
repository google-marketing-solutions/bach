`bach` can notify on success / failure of operations executed by [actor](actors.md).

## Built-in notification channels

### Slack


/// tab | cli
```bash hl_lines="3-5"
bach --area campaign_performance \
  --accounts GOOGLE_ACCOUNT_ID \
  --notify slack \
  --slack.channel=SLACK_CHANNEL \
  --slack.bot-token=$BACH_SLACK_BOT_TOKEN
```
///

### Email

### Telegram
```bash hl_lines="3-5"
bach --area campaign_performance \
  --accounts GOOGLE_ACCOUNT_ID \
  --notify telegram \
  --telegram.channel=TELEGRAM_CHANNEL \
  --telegram.bot-token=$TELEGRAM_SLACK_BOT_TOKEN
```
