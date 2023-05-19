import time
from .models import TaskExample


def dummy(t: TaskExample):
    print(f"=> The task will do: {t.do}, and it will wait for {t.wait}")
    time.sleep(t.wait)
    print(f"=> Dummy's task did")