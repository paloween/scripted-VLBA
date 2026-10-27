from vlbapipe.caltables import CalRegistry, CalTable


def T(path, order, kind=""):
    return CalTable(path=path, interp="nearest", stage=f"s{order}", order=order, kind=kind)


def test_apply_order_follows_stage_order():
    r = CalRegistry()
    r.add(T("late", 3))
    r.add(T("early", 1))
    assert r.gaintables() == ["early", "late"]


def test_exclude_kinds_and_before_order():
    r = CalRegistry([T("a", 1), T("tsys", 1, "tsys"), T("b", 2)])
    assert r.gaintables(exclude_kinds=("tsys",)) == ["a", "b"]
    assert r.gaintables(before_order=2) == ["a", "tsys"]


def test_roundtrip():
    r = CalRegistry([T("a", 1)])
    assert CalRegistry.from_list(r.to_list()).gaintables() == ["a"]
