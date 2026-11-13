import copy
from pathlib import Path
import pytest
from aetherpaper.model import load_project, validate_project, SceneError

EXAMPLE=Path(__file__).resolve().parents[1]/'examples/room_pickup.json'

def model():
    return copy.deepcopy(load_project(EXAMPLE).data)

def test_example_validates():
    proj=load_project(EXAMPLE)
    assert proj.duration==7.5
    assert len(proj.scenes)==1

@pytest.mark.parametrize('mutation,match',[
    (lambda p:p.update(version='0.2'),'version'),
    (lambda p:p['canvas'].update(fps=0),'fps'),
    (lambda p:p['canvas'].update(width=961),'width'),
    (lambda p:p['scenes'][0]['characters'][0].update(x=float('nan')),'finite'),
    (lambda p:p['scenes'][0]['actions'][1].update(prop='lost'),'unknown prop'),
    (lambda p:p['scenes'][0]['actions'][2].update(start=7.49,end=7.4),'later'),
    (lambda p:p['scenes'][0].update(duration=7.51),'multiple'),
    (lambda p:p['scenes'][0].update(background='yellow'),'#RRGGBB'),
])
def test_invalid_projects_rejected(mutation,match):
    project=model();mutation(project)
    with pytest.raises(SceneError,match=match):
        validate_project(project)

def test_duplicate_ids_rejected():
    project=model(); project['scenes'].append(copy.deepcopy(project['scenes'][0]))
    with pytest.raises(SceneError,match='duplicate scene id'):
        validate_project(project)
