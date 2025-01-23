from datetime import date

import pytest
from discord.ext.commands import BadArgument

from operationbot.converters import ArgDate


@pytest.mark.asyncio
async def test_argdate():
    constant_date = date(2020, 1, 1)
    date_this_year = date(date.today().year, 1, 1)
    ctx = None
    assert await ArgDate.convert(ctx, "2020-01-01") == constant_date
    assert await ArgDate.convert(ctx, "20-01-01") == constant_date
    assert await ArgDate.convert(ctx, "20200101") == constant_date
    assert await ArgDate.convert(ctx, "200101") == constant_date

    assert await ArgDate.convert(ctx, "01-01") == date_this_year
    assert await ArgDate.convert(ctx, "--0101") == date_this_year
    with pytest.raises(BadArgument):
        await ArgDate.convert(ctx, "0101")
    with pytest.raises(BadArgument):
        await ArgDate.convert(ctx, "2023-30-12")
