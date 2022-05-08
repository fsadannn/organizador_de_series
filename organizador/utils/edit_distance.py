from typing import List, Set, Text


def editDistance(a: str, b: str, lower: bool = False) -> int:
    """Distancia de Leventein entre dos cadenas de texto.
        a,b son string
        devuelve un int
    """
    if lower:
        a = a.lower()
        b = b.lower()

    m: List[List[int]] = []
    m.append([i for i in range(len(a) + 1)])

    for i in range(len(b)):
        m.append([i + 1] + [0 for i in range(len(a))])

    for i in range(1, len(b) + 1):
        for j in range(1, len(a) + 1):
            if a[j - 1] == b[i - 1]:
                m[i][j] = m[i - 1][j - 1]
            else:
                cte = 1
                if not a[j - 1].isalnum():
                    cte = 0.5
                m[i][j] = min(
                    m[i - 1][j - 1] + cte, min(m[i][j - 1] + 1, m[i - 1][j] + cte))

    ret = m[len(b)][len(a)]

    return ret


def best_ed(name: str, sett: Set[Text], gap: int = 2) -> Text:
    near = ''
    bedd = 100

    for j in sett:
        edd = editDistance(name, j, True)

        if edd <= gap and edd < bedd:
            near = j
            bedd = edd

            if edd == 0:
                break

    if near == '':
        return name

    return near
