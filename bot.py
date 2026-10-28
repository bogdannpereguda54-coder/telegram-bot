    async with aiohttp.ClientSession() as session:
        async with session.post(GRAMIX_URL, json=payload, headers=headers) as resp:
            if resp.status in (200, 201):
                return True, await resp.json()
            else:
                return False, await resp.text()
