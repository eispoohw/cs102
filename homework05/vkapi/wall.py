import textwrap
import time
import typing as tp
from string import Template

import pandas as pd
from pandas import json_normalize

from vkapi import config, session
from vkapi.exceptions import APIError


def get_posts_2500(
    owner_id: str = "",
    domain: str = "",
    offset: int = 0,
    count: int = 10,
    max_count: int = 2500,
    filter: str = "owner",
    extended: int = 0,
    fields: tp.Optional[tp.List[str]] = None,
) -> tp.Dict[str, tp.Any]:
    code = f"""
            var result = [];
            var i=0;
            var count=0;
            while (i < {max_count}){{
                if (i+{offset}+100>{count}){{
                var wall = API.wall.get({{"owner_id":"{owner_id}", "domain": "{domain}", "count":{count}-(i+{offset}), "fields":"{','.join(fields) if fields is not None else ''}", "extended": {extended}, "filter":"{filter}","offset": i+{offset}}});
                    result.push(wall.items);
                    count = wall.count;
                    i = {max_count};
                }}
                else{{
                    var wall = API.wall.get({{"owner_id":"{owner_id}", "domain": "{domain}", "count":100, "fields":"{','.join(fields) if fields is not None else ''}", "extended": {extended}, "filter":"{filter}", "offset": i+{offset}}});
                    result.push(wall.items);
                    count = wall.count;
                }}
                i = i+100;
            }}
            return {{"count": count, "items": result}};"""
    response = session.post(
        "execute",
        timeout=30,
        data={
            "access_token": config.VK_CONFIG["access_token"],
            "v": "5.126",
            "code": code,
        },
    )
    if "error" in response.json():
        raise APIError(response.json()["error"]["error_msg"])
    return response.json()


def get_wall_execute(
    owner_id: str = "",
    domain: str = "",
    offset: int = 0,
    count: int = 10,
    max_count: int = 2500,
    filter: str = "owner",
    extended: int = 0,
    fields: tp.Optional[tp.List[str]] = None,
    progress=None,
) -> pd.DataFrame:
    """
    Возвращает список записей со стены пользователя или сообщества.

    @see: https://vk.com/dev/wall.get

    :param owner_id: Идентификатор пользователя или сообщества, со стены которого необходимо получить записи.
    :param domain: Короткий адрес пользователя или сообщества.
    :param offset: Смещение, необходимое для выборки определенного подмножества записей.
    :param count: Количество записей, которое необходимо получить (0 - все записи).
    :param max_count: Максимальное число записей, которое может быть получено за один запрос.
    :param filter: Определяет, какие типы записей на стене необходимо получить.
    :param extended: 1 — в ответе будут возвращены дополнительные поля profiles и groups, содержащие информацию о пользователях и сообществах.
    :param fields: Список дополнительных полей для профилей и сообществ, которые необходимо вернуть.
    :param progress: Callback для отображения прогресса.
    """
    response = session.post(
        "execute",
        data={
            "access_token": config.VK_CONFIG["access_token"],
            "v": "5.126",
            "code": f'return {{"count": API.wall.get({{"owner_id": "{owner_id}", "filter":"{filter}", "domain": "{domain}", "count": "1"}}).count}};',
        },
    )
    if "error" in response.json():
        raise APIError(response.json()["error"]["error_msg"])
    if count != 0:
        count = min(count, response.json()["response"]["count"])
    else:
        count = response.json()["response"]["count"]
    if progress is None:
        progress = lambda x, *a, **kw: x
    json_data = []
    for j, i in progress(enumerate(range(offset, count, max_count))):
        response_json = get_posts_2500(
            owner_id, domain, offset + i, count, max_count, filter, extended, fields
        )
        res = []
        if isinstance(response_json, dict):
            for x in response_json["response"]["items"]:
                res.append(x)
            json_data.extend(res)
        time.sleep(1)
    return json_normalize(json_data)
