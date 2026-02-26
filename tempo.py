from time import sleep
async def arroz():
    await sleep(5)
    return "ok"

async def feijao():
    await sleep(2)
    return "ok"


def cozinhar():
    arroz()
    feijao()
    return "pronto"

cozinhar()
    