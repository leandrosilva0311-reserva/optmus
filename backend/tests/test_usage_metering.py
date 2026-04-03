from optimus_backend.infrastructure.billing.in_memory_usage_meter import InMemoryUsageMeter


def test_usage_meter_consumes_within_plan_limit() -> None:
    meter = InMemoryUsageMeter()
    allowed, consumed, limit = meter.consume(project_id="p1", plan_id="starter", units=1)
    assert allowed is True
    assert consumed == 1
    assert limit >= consumed


def test_usage_meter_blocks_when_limit_exceeded() -> None:
    meter = InMemoryUsageMeter()
    allowed, consumed, limit = meter.consume(project_id="p2", plan_id="starter", units=50)
    assert allowed is True
    assert consumed == limit

    allowed2, consumed2, limit2 = meter.consume(project_id="p2", plan_id="starter", units=1)
    assert allowed2 is False
    assert consumed2 == limit2
