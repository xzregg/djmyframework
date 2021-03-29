# -*- coding: utf-8 -*-
# @Time    : 2021-03-29 10:07
# @Author  : xzr
# @File    : fapi
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    : 

from typing import Optional

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}