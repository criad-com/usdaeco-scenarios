"""The narrative must retain defects and follow the measured artifact values."""
from usdaeco_scenarios.evidence import acceptance
from usdaeco_scenarios.walkthrough import ORDER, summary


def test_plan_b_defect_cannot_be_reported_as_clear():
    findings = [{'name': name, 'programme': 'A', 'occurrences': count, 'severity': 'error'}
                for name, count in [('AccessAfterEnclosure',4), ('WorkspaceOccupied',1), ('EnclosureBeforeInspection',2)]]
    findings += [dict(name='ProgrammeEvidence', programme=p, normalizedEqual=True) for p in ('A','B')]
    assert acceptance('plan', findings)[0]
    findings.append(dict(name='WorkspaceOccupied', programme='B', severity='error', occurrences=1))
    assert not acceptance('plan', findings)[0]
    assert 'Programme B reports 1' in summary('plan', findings)


def test_compliance_preserves_distinction_between_reader_and_clause_failures():
    findings = [dict(kind='summary', readers=11, **{'pass':10, 'fail':1, 'clause_failures':2})]
    assert acceptance('compliance', findings)[0]
    assert '2 clause failures' in summary('compliance', findings)
    findings[0]['fail'] = 0
    assert not acceptance('compliance', findings)[0]


def test_five_steps_have_contract_order():
    assert ORDER == ('cctv', 'clash', 'plan', 'compliance', 'repeat')


def test_repeat_measures_changed_partition_and_quantity_delta():
    findings = [dict(name='FloorDrift', all_changes={'changed': 1, 'extra': 1},
                     moved_walls=0, extra_doors=1),
                dict(name='ScheduleDelta', partition_length_m=3.2, doors=1)]
    assert acceptance('repeat', findings)[0]
    assert '1 changed wall' in summary('repeat', findings)
    findings[1]['partition_length_m'] = 0
    assert not acceptance('repeat', findings)[0]
