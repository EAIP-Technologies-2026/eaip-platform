from __future__ import annotations

import pydantic
import pytest

from eaip.bpm_engine.events import (
    ActivityCompleted,
    ActivityFailed,
    ActivityStarted,
    BpmEvent,
    ErrorEventTriggered,
    GatewayEvaluated,
    MessageReceived,
    ProcessCompleted,
    ProcessDeployed,
    ProcessFailed,
    ProcessStarted,
    SignalReceived,
    TimerFired,
)
from eaip.bpm_engine.exceptions import (
    ActivityExecutionError,
    BpmError,
    GatewayEvaluationError,
    MessageDeliveryError,
    ProcessDefinitionError,
    ProcessInstanceNotFoundError,
    SignalDeliveryError,
    TimerCancelledError,
)
from eaip.bpm_engine.health import BpmHealthCheck
from eaip.bpm_engine.integration import BpmRuntimeModule
from eaip.bpm_engine.models import (
    Activity,
    ActivityType,
    BpmnProcessDefinition,
    ExclusiveGateway,
    Gateway,
    GatewayType,
    InclusiveGateway,
    ParallelGateway,
    ProcessInstance,
    ProcessStatus,
    ProcessVariable,
    SequenceFlow,
    SequenceFlowCondition,
)
from eaip.bpm_engine.service import BpmService
from eaip.exceptions.base import ErrorCode
from eaip.health.checks import HealthStatus


class TestModels:
    def test_process_variable_defaults(self) -> None:
        v = ProcessVariable(name="var1")
        assert v.name == "var1"
        assert v.value is None
        assert v.type == "string"

    def test_process_variable_frozen(self) -> None:
        v = ProcessVariable(name="var1", value=42)
        with pytest.raises(pydantic.ValidationError):
            v.name = "var2"

    def test_process_variable_extra_forbidden(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            ProcessVariable(name="x", unknown="y")  # type: ignore[call-arg]

    def test_activity_defaults(self) -> None:
        a = Activity(id="a1", name="Task 1")
        assert a.type == ActivityType.TASK
        assert a.status.value == "pending"
        assert a.retry_count == 0
        assert a.input_params == {}

    def test_activity_with_type(self) -> None:
        a = Activity(id="a2", name="Service", type=ActivityType.SERVICE_TASK)
        assert a.type == ActivityType.SERVICE_TASK

    def test_gateway_defaults(self) -> None:
        g = Gateway(id="g1", name="Gateway 1", type=GatewayType.EXCLUSIVE)
        assert g.type == GatewayType.EXCLUSIVE
        assert g.default_flow_id == ""

    def test_exclusive_gateway(self) -> None:
        g = ExclusiveGateway(id="g1", name="XOR")
        assert g.type == GatewayType.EXCLUSIVE

    def test_parallel_gateway(self) -> None:
        g = ParallelGateway(id="g1", name="AND")
        assert g.type == GatewayType.PARALLEL

    def test_inclusive_gateway(self) -> None:
        g = InclusiveGateway(id="g1", name="OR")
        assert g.type == GatewayType.INCLUSIVE

    def test_sequence_flow(self) -> None:
        sf = SequenceFlow(id="sf1", source_id="a1", target_id="a2")
        assert sf.condition is None

    def test_sequence_flow_with_condition(self) -> None:
        cond = SequenceFlowCondition(expression="amount > 100", label="High value")
        sf = SequenceFlow(id="sf1", source_id="a1", target_id="a2", condition=cond)
        assert sf.condition is not None
        assert sf.condition.expression == "amount > 100"

    def test_bpmn_process_definition_defaults(self) -> None:
        d = BpmnProcessDefinition(id="d1", name="Process 1", key="process_1")
        assert d.version == 1
        assert d.is_executable is True
        assert d.activities == ()
        assert d.metadata == {}

    def test_bpmn_process_definition_with_activities(self) -> None:
        a1 = Activity(id="a1", name="Start")
        d = BpmnProcessDefinition(id="d1", name="Proc", key="proc", activities=(a1,))
        assert len(d.activities) == 1
        assert d.activities[0].name == "Start"

    def test_process_instance_defaults(self) -> None:
        inst = ProcessInstance(id="i1", process_definition_id="d1")
        assert inst.status == ProcessStatus.PENDING
        assert inst.variables == ()
        assert inst.active_activity_ids == ()
        assert inst.error_message == ""

    def test_process_instance_frozen(self) -> None:
        inst = ProcessInstance(id="i1", process_definition_id="d1")
        with pytest.raises(pydantic.ValidationError):
            inst.status = ProcessStatus.RUNNING


class TestEvents:
    def test_process_deployed_defaults(self) -> None:
        e = ProcessDeployed(process_definition_id="d1", process_name="P", version=1, key="p")
        assert e.event_type == "eaip.bpm_engine.process.deployed"
        assert e.version == 1

    def test_process_started_defaults(self) -> None:
        e = ProcessStarted(process_instance_id="i1", process_definition_id="d1", process_name="P")
        assert e.correlation_id == ""

    def test_process_completed_duration(self) -> None:
        e = ProcessCompleted(
            process_instance_id="i1",
            process_definition_id="d1",
            process_name="P",
            duration_ms=1500.0,
            completed_activities=3,
        )
        assert e.duration_ms == 1500.0
        assert e.completed_activities == 3

    def test_process_failed_error(self) -> None:
        e = ProcessFailed(
            process_instance_id="i1",
            process_definition_id="d1",
            process_name="P",
            error="timeout",
            failed_activity_id="a1",
        )
        assert e.error == "timeout"
        assert e.failed_activity_id == "a1"

    def test_activity_started(self) -> None:
        e = ActivityStarted(
            process_instance_id="i1",
            activity_id="a1",
            activity_name="Task",
            activity_type="task",
            attempt=1,
        )
        assert e.attempt == 1

    def test_activity_completed(self) -> None:
        e = ActivityCompleted(
            process_instance_id="i1",
            activity_id="a1",
            activity_name="Task",
            activity_type="task",
            duration_ms=500.0,
        )
        assert e.duration_ms == 500.0

    def test_activity_failed(self) -> None:
        e = ActivityFailed(
            process_instance_id="i1",
            activity_id="a1",
            activity_name="Task",
            activity_type="task",
            error="err",
            attempt=1,
            will_retry=True,
        )
        assert e.will_retry is True

    def test_gateway_evaluated(self) -> None:
        e = GatewayEvaluated(
            process_instance_id="i1",
            gateway_id="g1",
            gateway_name="XOR",
            gateway_type="exclusive",
            selected_flow_id="sf1",
            condition_result=True,
        )
        assert e.condition_result is True
        assert e.selected_flow_id == "sf1"

    def test_signal_received_defaults(self) -> None:
        e = SignalReceived(process_instance_id="i1", signal_name="sig")
        assert e.signal_payload == {}

    def test_signal_received_with_payload(self) -> None:
        e = SignalReceived(
            process_instance_id="i1",
            signal_name="sig",
            signal_payload={"key": "val"},
        )
        assert e.signal_payload == {"key": "val"}

    def test_message_received_defaults(self) -> None:
        e = MessageReceived(process_instance_id="i1", message_name="msg")
        assert e.message_payload == {}
        assert e.correlation_key == ""

    def test_timer_fired(self) -> None:
        e = TimerFired(
            process_instance_id="i1",
            activity_id="a1",
            timer_name="wait",
            timer_duration_seconds=60.0,
        )
        assert e.timer_duration_seconds == 60.0

    def test_error_event_triggered(self) -> None:
        e = ErrorEventTriggered(
            process_instance_id="i1",
            error_code="BPMN-001",
            error_message="invalid data",
            failed_activity_id="a1",
        )
        assert e.error_code == "BPMN-001"

    def test_events_frozen(self) -> None:
        e = ProcessStarted(process_instance_id="i1", process_definition_id="d1", process_name="P")
        with pytest.raises(pydantic.ValidationError):
            e.process_instance_id = "i2"

    def test_bpm_event_union(self) -> None:
        e: BpmEvent = ProcessDeployed(
            process_definition_id="d1", process_name="P", version=1, key="p"
        )
        assert isinstance(e, ProcessDeployed)


class TestExceptions:
    def test_bpm_error_base(self) -> None:
        err = BpmError("base error")
        assert err.code == ErrorCode.INTERNAL_ERROR

    def test_process_definition_error(self) -> None:
        err = ProcessDefinitionError("invalid definition", process_key="pk1")
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert err.process_key == "pk1"

    def test_process_instance_not_found(self) -> None:
        err = ProcessInstanceNotFoundError("i1")
        assert err.code == ErrorCode.NOT_FOUND
        assert "i1" in str(err)

    def test_activity_execution_error(self) -> None:
        err = ActivityExecutionError("a1", "something went wrong")
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert err.activity_id == "a1"

    def test_gateway_evaluation_error(self) -> None:
        err = GatewayEvaluationError("g1", "no matching condition")
        assert err.code == ErrorCode.VALIDATION_FAILED
        assert err.gateway_id == "g1"

    def test_signal_delivery_error(self) -> None:
        err = SignalDeliveryError("sig1", "instance not found")
        assert err.code == ErrorCode.GATEWAY_ERROR
        assert err.signal_name == "sig1"

    def test_message_delivery_error(self) -> None:
        err = MessageDeliveryError("msg1", "delivery failed")
        assert err.code == ErrorCode.GATEWAY_ERROR
        assert err.message_name == "msg1"

    def test_timer_cancelled_error(self) -> None:
        err = TimerCancelledError("t1")
        assert err.code == ErrorCode.INTERNAL_ERROR
        assert err.timer_id == "t1"

    def test_cause_chaining(self) -> None:
        cause = ValueError("root cause")
        err = BpmError("msg", cause=cause)
        assert err.__cause__ is cause

    def test_to_dict(self) -> None:
        err = ProcessInstanceNotFoundError("i1")
        d = err.to_dict()
        assert d["type"] == "ProcessInstanceNotFoundError"
        assert d["code"] == "EAIP-0003"

    def test_inheritance(self) -> None:
        assert issubclass(ProcessDefinitionError, BpmError)
        assert issubclass(ActivityExecutionError, BpmError)
        assert issubclass(GatewayEvaluationError, BpmError)
        assert issubclass(SignalDeliveryError, BpmError)
        assert issubclass(MessageDeliveryError, BpmError)
        assert issubclass(TimerCancelledError, BpmError)
        assert issubclass(ProcessInstanceNotFoundError, BpmError)


class TestBpmService:
    @pytest.fixture
    async def service(self) -> BpmService:
        return BpmService()

    @pytest.fixture
    def sample_definition(self) -> BpmnProcessDefinition:
        a1 = Activity(id="a1", name="Start Event")
        a2 = Activity(id="a2", name="Process Task")
        a3 = Activity(id="a3", name="End Event")
        return BpmnProcessDefinition(
            id="pd1",
            name="Sample Process",
            key="sample_process",
            activities=(a1, a2, a3),
        )

    async def test_deploy_definition(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        result = await service.deploy(sample_definition)
        assert result.id == "pd1"
        assert len(await service.list_definitions()) == 1

    async def test_deploy_duplicate_raises(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        with pytest.raises(ProcessDefinitionError):
            await service.deploy(sample_definition)

    async def test_start_process(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        assert instance.status == ProcessStatus.RUNNING
        assert instance.process_definition_id == "pd1"

    async def test_start_nonexistent_definition_raises(self, service: BpmService) -> None:
        with pytest.raises(ProcessDefinitionError):
            await service.start("nonexistent")

    async def test_get_instance(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        retrieved = await service.get_instance(instance.id)
        assert retrieved.id == instance.id

    async def test_get_nonexistent_instance_raises(self, service: BpmService) -> None:
        with pytest.raises(ProcessInstanceNotFoundError):
            await service.get_instance("nonexistent")

    async def test_complete_activity(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        updated = await service.complete_activity(instance.id, "a1", duration_ms=100.0)
        assert "a1" not in updated.active_activity_ids
        assert "a1" in updated.completed_activity_ids

    async def test_fail_activity(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        updated = await service.fail_activity(instance.id, "a1", "error", will_retry=False)
        assert updated.status == ProcessStatus.FAILED
        assert "error" in updated.error_message

    async def test_signal_running_instance(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        result = await service.signal(instance.id, "my_signal", {"data": 1})
        assert result.id == instance.id

    async def test_signal_stopped_instance_raises(self, service: BpmService) -> None:
        with pytest.raises(ProcessInstanceNotFoundError):
            await service.signal("nonexistent", "sig")

    async def test_send_message(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        result = await service.send_message(instance.id, "my_msg", {"key": "val"}, "corr1")
        assert result.id == instance.id

    async def test_evaluate_gateway(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        result = await service.evaluate_gateway(instance.id, "g1", "sf1", condition_result=True)
        assert result.id == instance.id

    async def test_fire_timer(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        result = await service.fire_timer(instance.id, "a1", "timer1", 30.0)
        assert result.id == instance.id

    async def test_trigger_error_event(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        result = await service.trigger_error_event(instance.id, "ERR-001", "error msg", "a1")
        assert result.id == instance.id

    async def test_list_instances_by_status(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        await service.start("pd1")
        running = await service.list_instances(status=ProcessStatus.RUNNING)
        assert len(running) == 1

    async def test_list_definitions(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        defs = await service.list_definitions()
        assert len(defs) == 1

    async def test_complete_process(
        self,
        service: BpmService,
        sample_definition: BpmnProcessDefinition,
    ) -> None:
        await service.deploy(sample_definition)
        instance = await service.start("pd1")
        for act_id in ("a1", "a2", "a3"):
            await service.complete_activity(instance.id, act_id, duration_ms=50.0)
        completed = await service.get_instance(instance.id)
        assert completed.status == ProcessStatus.COMPLETED


class TestBpmHealthCheck:
    async def test_healthy_when_no_failures(self) -> None:
        service = BpmService()
        health = BpmHealthCheck(service=service)
        report = await health.check()
        assert report.status == HealthStatus.HEALTHY

    async def test_degraded_when_failures_exist(self) -> None:
        service = BpmService()
        a1 = Activity(id="a1", name="Task")
        definition = BpmnProcessDefinition(id="pd1", name="Proc", key="proc", activities=(a1,))
        await service.deploy(definition)
        instance = await service.start("pd1")
        await service.fail_activity(instance.id, "a1", "failure", will_retry=False)
        health = BpmHealthCheck(service=service)
        report = await health.check()
        assert report.status == HealthStatus.DEGRADED

    async def test_health_details(self) -> None:
        service = BpmService()
        health = BpmHealthCheck(service=service)
        report = await health.check()
        assert "definitions_deployed" in report.details


class TestBpmRuntimeModule:
    def test_name(self) -> None:
        mod = BpmRuntimeModule()
        assert mod.name == "bpm_engine"

    def test_service_property(self) -> None:
        svc = BpmService()
        mod = BpmRuntimeModule(service=svc)
        assert mod.service is svc

    def test_default_service(self) -> None:
        mod = BpmRuntimeModule()
        assert isinstance(mod.service, BpmService)
