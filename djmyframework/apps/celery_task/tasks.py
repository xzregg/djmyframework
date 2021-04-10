# -*- coding: utf-8 -*-


from config.celery_app import app, Task

@app.task(bind=True, ignore_result=True)
def test_live(self: Task):
    """
    测试 celery
    :param self:
    :return:
    """
    return True
