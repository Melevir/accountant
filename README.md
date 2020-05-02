# Accountant

Set of scripts for personal financial evaluation.


## `check_periodic_payments.py`

Script that checks payments history and tries to find recurrent payments (subscriptions, etc).

Supports only Tinkoff export format.

Sample usage:

```bash
python check_periodic_payments.py --sure_recurrent_payments_descriptions=nuzhnapomosh ~/Downloads/ops.csv
```
