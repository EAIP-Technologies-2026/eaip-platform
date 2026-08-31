from __future__ import annotations

from eaip.notifications.center import NotificationCenter, NotificationFilter
from eaip.notifications.models import (
    Notification,
    NotificationCategory,
    NotificationChannel,
    NotificationSeverity,
    NotificationStatus,
)


class TestNotificationCenter:
    def test_deliver_adds_to_inbox(self) -> None:
        center = NotificationCenter()
        notification = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.IN_APP,
            recipients=("user1",),
            subject="test",
        )
        center.deliver(notification)
        inbox = center.get_inbox("user1")
        assert len(inbox) == 1
        assert inbox[0].status == NotificationStatus.DELIVERED

    def test_get_inbox_unread_only(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s1"
        )
        n2 = Notification(
            id="n2", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s2"
        )
        center.deliver(n1)
        center.deliver(n2)
        center.mark_read("u1", "n1")
        unread = center.get_inbox("u1", unread_only=True)
        assert len(unread) == 1
        assert unread[0].id == "n2"

    def test_mark_read(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        result = center.mark_read("u1", "n1")
        assert result is True
        assert center.get_unread_count("u1") == 0

    def test_mark_read_nonexistent(self) -> None:
        center = NotificationCenter()
        result = center.mark_read("u1", "nonexistent")
        assert result is False

    def test_mark_all_read(self) -> None:
        center = NotificationCenter()
        for i in range(3):
            n = Notification(
                id=f"n{i}",
                type="a",
                channel=NotificationChannel.IN_APP,
                recipients=("u1",),
                subject=f"s{i}",
            )
            center.deliver(n)
        count = center.mark_all_read("u1")
        assert count == 3
        assert center.get_unread_count("u1") == 0

    def test_get_unread_count(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        assert center.get_unread_count("u1") == 1
        center.mark_read("u1", "n1")
        assert center.get_unread_count("u1") == 0

    def test_delete_notification(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        result = center.delete_notification("u1", "n1")
        assert result is True
        assert len(center.get_inbox("u1")) == 0

    def test_get_inbox_with_channel_filter(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s1"
        )
        n2 = Notification(
            id="n2", type="a", channel=NotificationChannel.EMAIL, recipients=("u1",), subject="s2"
        )
        center.deliver(n1)
        center.deliver(n2)
        email = center.get_inbox("u1", channel=NotificationChannel.EMAIL)
        assert len(email) == 1
        assert email[0].id == "n2"

    def test_severity_filter(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s1",
            severity=NotificationSeverity.INFO,
        )
        n2 = Notification(
            id="n2",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s2",
            severity=NotificationSeverity.ERROR,
        )
        center.deliver(n1)
        center.deliver(n2)
        errors = center.get_inbox("u1", severity=NotificationSeverity.ERROR)
        assert len(errors) == 1
        assert errors[0].id == "n2"

    def test_category_filter(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s1",
            category=NotificationCategory.SYSTEM,
        )
        n2 = Notification(
            id="n2",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s2",
            category=NotificationCategory.SECURITY,
        )
        center.deliver(n1)
        center.deliver(n2)
        security = center.get_inbox("u1", category=NotificationCategory.SECURITY)
        assert len(security) == 1
        assert security[0].id == "n2"

    def test_search_filter(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="Deployment successful",
            body="All services deployed",
        )
        n2 = Notification(
            id="n2",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="Security alert",
            body="Unauthorized access detected",
        )
        center.deliver(n1)
        center.deliver(n2)
        results = center.get_inbox("u1", search_query="deployment")
        assert len(results) == 1
        assert results[0].id == "n1"

    def test_search_filter_body(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="Alert",
            body="Database connection failed",
        )
        center.deliver(n1)
        results = center.get_inbox("u1", search_query="database")
        assert len(results) == 1

    def test_group_key_filter(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s1",
            group_key="deploy-123",
        )
        n2 = Notification(
            id="n2",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s2",
            group_key="deploy-456",
        )
        center.deliver(n1)
        center.deliver(n2)
        results = center.get_inbox("u1", group_key="deploy-123")
        assert len(results) == 1
        assert results[0].id == "n1"

    def test_acknowledge(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        result = center.acknowledge("u1", "n1")
        assert result is True
        inbox = center.get_inbox("u1")
        assert inbox[0].status == NotificationStatus.ACKNOWLEDGED
        assert inbox[0].acknowledged_at is not None

    def test_acknowledge_already_acknowledged(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        center.acknowledge("u1", "n1")
        result = center.acknowledge("u1", "n1")
        assert result is False

    def test_dismiss(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        result = center.dismiss("u1", "n1")
        assert result is True
        inbox = center.get_inbox("u1")
        assert inbox[0].status == NotificationStatus.DISMISSED
        assert inbox[0].dismissed_at is not None

    def test_dismiss_already_dismissed(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s"
        )
        center.deliver(n)
        center.dismiss("u1", "n1")
        result = center.dismiss("u1", "n1")
        assert result is False

    def test_get_counts(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s1"
        )
        n2 = Notification(
            id="n2", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s2"
        )
        n3 = Notification(
            id="n3", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s3"
        )
        center.deliver(n1)
        center.deliver(n2)
        center.deliver(n3)
        center.mark_read("u1", "n1")
        center.acknowledge("u1", "n2")
        counts = center.get_counts("u1")
        assert counts["total"] == 3
        assert counts["unread"] == 1
        assert counts["acknowledged"] == 1
        assert counts["dismissed"] == 0

    def test_get_category_counts(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s1",
            category=NotificationCategory.SYSTEM,
        )
        n2 = Notification(
            id="n2",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s2",
            category=NotificationCategory.SECURITY,
        )
        n3 = Notification(
            id="n3",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s3",
            category=NotificationCategory.SYSTEM,
        )
        center.deliver(n1)
        center.deliver(n2)
        center.deliver(n3)
        counts = center.get_category_counts("u1")
        assert counts["system"] == 2
        assert counts["security"] == 1

    def test_get_severity_counts(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s1",
            severity=NotificationSeverity.INFO,
        )
        n2 = Notification(
            id="n2",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s2",
            severity=NotificationSeverity.ERROR,
        )
        center.deliver(n1)
        center.deliver(n2)
        counts = center.get_severity_counts("u1")
        assert counts["info"] == 1
        assert counts["error"] == 1

    def test_get_notification(self) -> None:
        center = NotificationCenter()
        n = Notification(
            id="n1",
            type="a",
            channel=NotificationChannel.IN_APP,
            recipients=("u1",),
            subject="s",
            summary="summary",
            deep_link="/dashboard",
            related_entity_id="entity-1",
            related_entity_type="deployment",
        )
        center.deliver(n)
        result = center.get_notification("u1", "n1")
        assert result is not None
        assert result.id == "n1"
        assert result.summary == "summary"
        assert result.deep_link == "/dashboard"

    def test_get_notification_nonexistent(self) -> None:
        center = NotificationCenter()
        result = center.get_notification("u1", "nonexistent")
        assert result is None

    def test_unread_count_excludes_acknowledged_and_dismissed(self) -> None:
        center = NotificationCenter()
        n1 = Notification(
            id="n1", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s1"
        )
        n2 = Notification(
            id="n2", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s2"
        )
        n3 = Notification(
            id="n3", type="a", channel=NotificationChannel.IN_APP, recipients=("u1",), subject="s3"
        )
        center.deliver(n1)
        center.deliver(n2)
        center.deliver(n3)
        center.acknowledge("u1", "n1")
        center.dismiss("u1", "n2")
        assert center.get_unread_count("u1") == 1

    def test_notification_filter_dataclass(self) -> None:
        f = NotificationFilter(
            unread_only=True,
            severity=NotificationSeverity.ERROR,
            category=NotificationCategory.SECURITY,
            search_query="test",
        )
        assert f.unread_only is True
        assert f.severity == NotificationSeverity.ERROR
        assert f.category == NotificationCategory.SECURITY
        assert f.search_query == "test"


class TestNotificationModels:
    def test_notification_with_new_fields(self) -> None:
        n = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.IN_APP,
            recipients=("user1",),
            subject="Test",
            body="Body",
            summary="Summary",
            severity=NotificationSeverity.WARNING,
            category=NotificationCategory.DEPLOYMENT,
            tenant_id="tenant-1",
            organization_id="org-1",
            source="deployment-service",
            deep_link="/deployments/123",
            related_entity_id="deploy-123",
            related_entity_type="deployment",
            group_key="deploy-group-1",
        )
        assert n.severity == NotificationSeverity.WARNING
        assert n.category == NotificationCategory.DEPLOYMENT
        assert n.tenant_id == "tenant-1"
        assert n.deep_link == "/deployments/123"
        assert n.group_key == "deploy-group-1"

    def test_notification_default_values(self) -> None:
        n = Notification(
            id="n1",
            type="alert",
            channel=NotificationChannel.IN_APP,
            recipients=("user1",),
            subject="Test",
        )
        assert n.severity == NotificationSeverity.INFO
        assert n.category == NotificationCategory.SYSTEM
        assert n.summary == ""
        assert n.tenant_id is None
        assert n.deep_link is None
        assert n.group_key is None

    def test_notification_status_acknowledged(self) -> None:
        assert NotificationStatus.ACKNOWLEDGED == "acknowledged"
        assert NotificationStatus.DISMISSED == "dismissed"

    def test_notification_severity_values(self) -> None:
        assert NotificationSeverity.INFO == "info"
        assert NotificationSeverity.SUCCESS == "success"
        assert NotificationSeverity.WARNING == "warning"
        assert NotificationSeverity.ERROR == "error"
        assert NotificationSeverity.CRITICAL == "critical"

    def test_notification_category_values(self) -> None:
        assert NotificationCategory.SYSTEM == "system"
        assert NotificationCategory.SECURITY == "security"
        assert NotificationCategory.OPERATIONS == "operations"
        assert NotificationCategory.APPROVALS == "approvals"
        assert NotificationCategory.AUTOMATION == "automation"
        assert NotificationCategory.WORKFLOW == "workflow"
        assert NotificationCategory.DEPLOYMENT == "deployment"
        assert NotificationCategory.KNOWLEDGE == "knowledge"
        assert NotificationCategory.CONDUCTOR == "conductor"
