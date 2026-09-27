from __future__ import annotations
import copy
import unittest
from pathlib import Path

from robo_dados_publicos.research.task255_task254_redirect_location_probe import (
    Task255Stop,
    execute_probe,
    load_config,
    load_evidence,
    validate_live_authorization,
)

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/"config/task255_task254_redirect_location_probe.v1.json"
EV=ROOT/"docs/evidence/TASK_255_TASK254_REDIRECT_INCIDENT_CANONICAL_0.8.0.json"
IMPL="5dbb0a3a8dc68cc286a1b6933dfbea94e7cab9d2"

class FakeTransport:
    def __init__(self,meta): self.meta=meta; self.calls=0
    def get(self,url,*,timeout,max_body_bytes):
        self.calls+=1
        return dict(self.meta)

def auth(cfg,impl=IMPL):
    return {
        "task":"TASK_255_LIVE_AUTHORIZATION",
        "repository":"ferinbon-cpu/robo-dados-publicos",
        "implementation_branch":"main",
        "runtime_branch":cfg["runtime"]["branch"],
        "implementation_sha":impl,
        "operation":"EXACT_1_TASK254_FIRST_TARGET_NOFOLLOW_REDIRECT_LOCATION_PROBE",
        "control":cfg["probe"]["control"],
        "requested_url":cfg["probe"]["requested_url"],
        "max_remote_get_count":1,
        "attempt_count":1,
        "owner_authorized":True,
        "source_network_authorized":True,
        "follow_redirects":False,
        "automatic_retry":False,
        "alternate_url_discovery":False,
        "prior_authorization_reused":False,
        "drive_write_authorized":False,
        "publication_authorized":False,
        "serving_authorized":False,
        "promotion_authorized":False,
        "recurrence_authorized":False,
        "schedule_authorized":False,
        "consumed":False,
    }

class Task255Test(unittest.TestCase):
    def setUp(self):
        self.cfg=load_config(CFG); self.ev=load_evidence(EV)

    def test_missing_auth_stops(self):
        self.assertEqual(validate_live_authorization(None,expected_implementation_sha=IMPL,config=self.cfg)["status"],"STOP_TASK255_LIVE_NOT_AUTHORIZED")

    def test_exact_auth_passes(self):
        self.assertEqual(validate_live_authorization(auth(self.cfg),expected_implementation_sha=IMPL,config=self.cfg),{"status":"PASS_TASK255_LIVE_AUTHORIZATION"})

    def test_redirect_location_captured(self):
        meta={"requested_url":self.cfg["probe"]["requested_url"],"http_status":302,"location":"https://example.gov.br/x","content_type":"text/html","bytes_received":0,"body_sha256":None,"transport_error":"HTTP_ERROR_302","remote_get_count":1}
        result=execute_probe(self.cfg,self.ev,transport=FakeTransport(meta),authorization=None,expected_implementation_sha=IMPL,offline_test_mode=True)
        self.assertEqual(result["status"],"PASS_TASK255_SINGLE_NOFOLLOW_PROBE_OBSERVED")
        self.assertEqual(result["outcome"],"REDIRECT_LOCATION_CAPTURED")
        self.assertFalse(result["redirect_followed"])
        self.assertFalse(result["remaining_seven_targets_queried"])

    def test_redirect_without_location_stops(self):
        meta={"requested_url":self.cfg["probe"]["requested_url"],"http_status":302,"location":None,"content_type":None,"bytes_received":0,"body_sha256":None,"transport_error":"HTTP_ERROR_302","remote_get_count":1}
        with self.assertRaisesRegex(Task255Stop,"TASK255_REDIRECT_LOCATION_MISSING"):
            execute_probe(self.cfg,self.ev,transport=FakeTransport(meta),authorization=None,expected_implementation_sha=IMPL,offline_test_mode=True)

    def test_non_https_location_stops(self):
        meta={"requested_url":self.cfg["probe"]["requested_url"],"http_status":302,"location":"http://example.com/x","content_type":None,"bytes_received":0,"body_sha256":None,"transport_error":"HTTP_ERROR_302","remote_get_count":1}
        with self.assertRaisesRegex(Task255Stop,"TASK255_REDIRECT_LOCATION_NOT_ABSOLUTE_HTTPS"):
            execute_probe(self.cfg,self.ev,transport=FakeTransport(meta),authorization=None,expected_implementation_sha=IMPL,offline_test_mode=True)

    def test_200_is_observation_not_redirect_inference(self):
        meta={"requested_url":self.cfg["probe"]["requested_url"],"http_status":200,"location":None,"content_type":"application/json","bytes_received":123,"body_sha256":"a"*64,"transport_error":None,"remote_get_count":1}
        result=execute_probe(self.cfg,self.ev,transport=FakeTransport(meta),authorization=None,expected_implementation_sha=IMPL,offline_test_mode=True)
        self.assertEqual(result["outcome"],"HTTP_200_NO_REDIRECT_CURRENTLY_OBSERVED")
        self.assertFalse(result["remaining_target_url_inference_allowed"])

if __name__=="__main__":
    unittest.main()
