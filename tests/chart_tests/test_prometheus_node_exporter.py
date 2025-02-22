import pytest

from tests import supported_k8s_versions, get_containers_by_name
from tests.chart_tests.helm_template_generator import render_chart


@pytest.mark.parametrize(
    "kube_version",
    supported_k8s_versions,
)
class TestPrometheusNodeExporterDaemonset:
    def test_prometheus_node_exporter_service_defaults(self, kube_version):
        docs = render_chart(
            kube_version=kube_version,
            show_only=["charts/prometheus-node-exporter/templates/service.yaml"],
        )

        assert len(docs) == 1
        doc = docs[0]
        assert doc["kind"] == "Service"
        assert doc["metadata"]["name"] == "release-name-prometheus-node-exporter"
        assert doc["spec"]["selector"]["app"] == "prometheus-node-exporter"
        assert doc["spec"]["type"] == "ClusterIP"
        assert doc["spec"]["ports"] == [
            {
                "port": 9100,
                "targetPort": 9100,
                "protocol": "TCP",
                "name": "metrics",
                "appProtocol": "tcp",
            }
        ]

    def test_prometheus_node_exporter_daemonset_defaults(self, kube_version):
        docs = render_chart(
            kube_version=kube_version,
            show_only=["charts/prometheus-node-exporter/templates/daemonset.yaml"],
        )

        assert len(docs) == 1
        doc = docs[0]
        assert doc["kind"] == "DaemonSet"
        assert doc["metadata"]["name"] == "release-name-prometheus-node-exporter"
        assert (
            doc["spec"]["selector"]["matchLabels"]["app"] == "prometheus-node-exporter"
        )
        assert (
            doc["spec"]["template"]["metadata"]["labels"]["app"]
            == "prometheus-node-exporter"
        )

        c_by_name = get_containers_by_name(doc)
        assert c_by_name["node-exporter"]
        assert c_by_name["node-exporter"]["resources"] == {
            "limits": {"cpu": "100m", "memory": "128Mi"},
            "requests": {"cpu": "10m", "memory": "128Mi"},
        }

    def test_prometheus_node_exporter_daemonset_custom_resources(self, kube_version):
        doc = render_chart(
            kube_version=kube_version,
            values={
                "prometheus-node-exporter": {
                    "resources": {
                        "limits": {"cpu": "777m", "memory": "999Mi"},
                        "requests": {"cpu": "666m", "memory": "888Mi"},
                    }
                },
            },
            show_only=["charts/prometheus-node-exporter/templates/daemonset.yaml"],
        )[0]

        assert doc["kind"] == "DaemonSet"
        assert doc["metadata"]["name"] == "release-name-prometheus-node-exporter"

        c_by_name = get_containers_by_name(doc)
        assert c_by_name["node-exporter"]
        assert c_by_name["node-exporter"]["resources"] == {
            "limits": {"cpu": "777m", "memory": "999Mi"},
            "requests": {"cpu": "666m", "memory": "888Mi"},
        }
        assert c_by_name["node-exporter"]["securityContext"] == {"runAsNonRoot": True}

    def test_prometheus_node_exporter_daemonset_with_security_context_overrides(
        self, kube_version
    ):
        doc = render_chart(
            kube_version=kube_version,
            values={
                "prometheus-node-exporter": {
                    "securityContext": {
                        "allowPrivilegeEscalation": False,
                        "readOnlyRootFilesystem": True,
                    }
                },
            },
            show_only=["charts/prometheus-node-exporter/templates/daemonset.yaml"],
        )[0]

        assert doc["kind"] == "DaemonSet"
        assert doc["metadata"]["name"] == "release-name-prometheus-node-exporter"

        c_by_name = get_containers_by_name(doc)
        assert c_by_name["node-exporter"]
        assert c_by_name["node-exporter"]["securityContext"] == {
            "allowPrivilegeEscalation": False,
            "readOnlyRootFilesystem": True,
            "runAsNonRoot": True,
        }
