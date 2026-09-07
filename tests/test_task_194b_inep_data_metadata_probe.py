import gzip
import json
import unittest

from scripts.task194b_inep_data_metadata_probe import (
    Task194BStop,
    _decode_http_body,
    bootstrap_metadata,
    decode_report_token,
    exact_auth_comment,
    sanitize_models,
)

REPORT_URL = "https://app.powerbi.com/view?r=eyJrIjoiN2ViNDBjNDEtMTM0OC00ZmFhLWIyZWYtZjI1YjU0NzQzMTJhIiwidCI6IjI2ZjczODk3LWM4YWMtNGIxZS05NzhmLWVhNGMwNzc0MzRiZiJ9"


class TestTask194BInepDataMetadataProbe(unittest.TestCase):
    def test_gzip_body_is_decompressed_offline(self):
        payload = json.dumps({"models":[{"id":"x"}]}).encode("utf-8")
        compressed = gzip.compress(payload)
        self.assertEqual(_decode_http_body(compressed, "gzip"), payload)
        self.assertEqual(_decode_http_body(compressed, ""), payload)
        self.assertEqual(_decode_http_body(payload, ""), payload)

    def test_report_token_is_exact(self):
        got=decode_report_token(REPORT_URL)
        self.assertEqual(got["resource_key"],"7eb40c41-1348-4faa-b2ef-f25b5474312a")
        self.assertEqual(got["tenant_id"],"26f73897-c8ac-4b1e-978f-ea4c077434bf")

    def test_exact_auth_comment(self):
        sha="a"*40
        self.assertEqual(
            exact_auth_comment(sha),
            f"TASK194D_INEP_DATA_METADATA_AUTHORIZED main={sha} issue=605 max_http_requests=2 querydata=0",
        )

    def test_bootstrap_extracts_only_pinned_report(self):
        html = """
        <script>
        var resourceKey = '7eb40c41-1348-4faa-b2ef-f25b5474312a';
        var tenantId = '26f73897-c8ac-4b1e-978f-ea4c077434bf';
        var resolvedClusterUri = 'https://wabi-test-b-primary-redirect.analysis.windows.net/';
        var telemetrySessionId = '11111111-1111-1111-1111-111111111111';
        function getModelsAndExploration() { var activityId = telemetrySessionId; var requestId = '22222222-2222-2222-2222-222222222222'; }
        </script>
        """
        got=bootstrap_metadata(
            html,
            "7eb40c41-1348-4faa-b2ef-f25b5474312a",
            "26f73897-c8ac-4b1e-978f-ea4c077434bf",
        )
        self.assertEqual(got["cluster_api"],"https://wabi-test-b-primary-api.analysis.windows.net")
        self.assertEqual(got["activity_id"],"11111111-1111-1111-1111-111111111111")
        self.assertEqual(got["request_id"],"22222222-2222-2222-2222-222222222222")

        alternate=bootstrap_metadata(
            html,
            "00000000-0000-0000-0000-000000000000",
            "11111111-1111-1111-1111-111111111111",
        )
        self.assertEqual(alternate["resource_key"],"00000000-0000-0000-0000-000000000000")

    def test_sanitizer_keeps_keyword_visual_metadata_only(self):
        title_config={
            "singleVisual":{
                "visualType":"card",
                "vcObjects":{
                    "title":[{"properties":{"text":{"expr":{"Literal":{"Value":"'Número de Turmas'"}}}}}]
                }
            }
        }
        models={
            "models":[{"id":"123","dbName":"db"}],
            "exploration":{
                "report":{"objectId":"report-1","name":"Censo"},
                "sections":[
                    {
                        "name":"page1",
                        "displayName":"Turmas",
                        "visualContainers":[
                            {
                                "config":__import__("json").dumps(title_config),
                                "query":__import__("json").dumps({"Commands":[{"SemanticQueryDataShapeCommand":{"Query":{"Version":2}}}]}),
                            },
                            {
                                "config":__import__("json").dumps({"singleVisual":{"visualType":"image"}}),
                            },
                        ],
                    }
                ],
            },
        }
        got=sanitize_models(models,["turma","munic"])
        self.assertEqual(got["section_count"],1)
        self.assertEqual(got["visual_count"],2)
        self.assertEqual(got["keyword_visual_count"],2)
        titled=[x for x in got["keyword_visuals"] if x["title"] == "Número de Turmas"]
        self.assertEqual(len(titled),1)
        self.assertFalse(got["querydata_called"])
        self.assertFalse(got["raw_payload_persisted"])


if __name__ == "__main__":
    unittest.main()
