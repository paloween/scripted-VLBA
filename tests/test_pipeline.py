import pytest

from vlbapipe.pipeline import Pipeline


@pytest.fixture(autouse=True)
def no_download(monkeypatch):
    # priorcals shells out to curl for the EOP file; skip the network in tests
    monkeypatch.setattr("vlbapipe.stages.priorcals.subprocess.run",
                        lambda *a, **k: None)


def test_stage_requires_predecessor(config, casa):
    with pytest.raises(RuntimeError, match="requires"):
        Pipeline(config, casa).run(["priorcals"])


def test_full_run_registers_tables_in_order(config, casa):
    p = Pipeline(config, casa)
    p.run()
    names = [t.rsplit("/", 1)[-1] for t in p.ctx.registry.gaintables()]
    assert names == ["t_smooth.accor", "t.gcal", "t.tsys"]  # no EOP: download skipped
    assert p.ctx.completed == ["importdata", "priorcals"]
    assert any("EOP" in w for w in p.ctx.warnings)


def test_resume_in_new_session_restores_tables(config, casa):
    Pipeline(config, casa).run()
    resumed = Pipeline(config, casa)  # fresh object, state loaded from disk
    assert resumed.ctx.completed == ["importdata", "priorcals"]
    assert len(resumed.ctx.registry.gaintables()) == 3


def test_auto_refant(config, casa):
    from dataclasses import replace
    p = Pipeline(replace(config, refant="auto"), casa)
    p.run(["importdata"])
    assert p.ctx.refant == "FD,PT"


def test_export_script(config, casa, tmp_path):
    p = Pipeline(config, casa)
    p.run()
    out = tmp_path / "script.py"
    p.export_script(str(out))
    assert "importfitsidi(" in out.read_text()
