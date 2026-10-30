import os
import json
import time
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

from app.config import settings
from app.schemas.models import InterviewSession, ResumeAnalysis, LinkInspectionResult

class SessionStore:
    """
    Hybrid Session Store for ResumeGrind.
    Provides persistence via AWS DynamoDB for production/serverless Lambda execution,
    with automatic in-memory fallback for local development or disconnected mode.
    """

    def __init__(self):
        self._memory_sessions: Dict[str, Dict[str, Any]] = {}
        self._memory_resumes: Dict[str, Dict[str, Any]] = {}
        self._memory_inspections: Dict[str, Dict[str, Any]] = {}
        self.table_name = settings.DYNAMODB_TABLE_NAME
        self.region = settings.AWS_REGION
        self._dynamodb_resource = None
        self._table = None
        self._dynamodb_enabled = False
        self._init_dynamodb()

    def _init_dynamodb(self):
        try:
            # Check if environment or credentials exist
            session = boto3.Session(region_name=self.region)
            credentials = session.get_credentials()
            if credentials:
                self._dynamodb_resource = session.resource('dynamodb')
                self._table = self._dynamodb_resource.Table(self.table_name)
                # Verify accessibility
                self._table.load()
                self._dynamodb_enabled = True
                print(f"[SESSION STORE] DynamoDB connected successfully to table '{self.table_name}'.")
            else:
                self._dynamodb_enabled = False
                print("[SESSION STORE] No AWS credentials found; running with in-memory persistence fallback.")
        except Exception as e:
            self._dynamodb_enabled = False
            print(f"[SESSION STORE] DynamoDB initialization skipped ({e}); using in-memory store.")

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------
    async def save_session(self, session: InterviewSession) -> None:
        session_id = session.session_id
        session_dict = session.model_dump()
        self._memory_sessions[session_id] = session_dict

        if self._dynamodb_enabled and self._table:
            try:
                # Add TTL timestamp (24 hours from now)
                ttl_timestamp = int(time.time()) + 86400
                item = {
                    "pk": f"SESSION#{session_id}",
                    "sk": "METADATA",
                    "type": "interview_session",
                    "data": json.dumps(session_dict),
                    "ttl": ttl_timestamp
                }
                self._table.put_item(Item=item)
            except Exception as e:
                print(f"[SESSION STORE] DynamoDB put_item failed for session {session_id}: {e}")

    async def get_session(self, session_id: str) -> Optional[InterviewSession]:
        if self._dynamodb_enabled and self._table:
            try:
                response = self._table.get_item(
                    Key={"pk": f"SESSION#{session_id}", "sk": "METADATA"}
                )
                item = response.get("Item")
                if item and "data" in item:
                    data = json.loads(item["data"])
                    return InterviewSession.model_validate(data)
            except Exception as e:
                print(f"[SESSION STORE] DynamoDB get_item failed for session {session_id}: {e}")

        mem_data = self._memory_sessions.get(session_id)
        if mem_data:
            return InterviewSession.model_validate(mem_data)
        return None

    # -------------------------------------------------------------------------
    # Resumes
    # -------------------------------------------------------------------------
    async def save_resume(self, session_id: str, resume: ResumeAnalysis) -> None:
        resume_dict = resume.model_dump()
        self._memory_resumes[session_id] = resume_dict

        if self._dynamodb_enabled and self._table:
            try:
                ttl_timestamp = int(time.time()) + 86400
                item = {
                    "pk": f"SESSION#{session_id}",
                    "sk": "RESUME",
                    "type": "resume_analysis",
                    "data": json.dumps(resume_dict),
                    "ttl": ttl_timestamp
                }
                self._table.put_item(Item=item)
            except Exception as e:
                print(f"[SESSION STORE] DynamoDB save_resume failed: {e}")

    async def get_resume(self, session_id: str) -> Optional[ResumeAnalysis]:
        if self._dynamodb_enabled and self._table:
            try:
                response = self._table.get_item(
                    Key={"pk": f"SESSION#{session_id}", "sk": "RESUME"}
                )
                item = response.get("Item")
                if item and "data" in item:
                    return ResumeAnalysis.model_validate(json.loads(item["data"]))
            except Exception as e:
                print(f"[SESSION STORE] DynamoDB get_resume failed: {e}")

        mem_data = self._memory_resumes.get(session_id)
        if mem_data:
            return ResumeAnalysis.model_validate(mem_data)
        return None

    # -------------------------------------------------------------------------
    # Inspections
    # -------------------------------------------------------------------------
    async def save_inspection(self, session_id: str, inspection: LinkInspectionResult) -> None:
        inspection_dict = inspection.model_dump()
        self._memory_inspections[session_id] = inspection_dict

        if self._dynamodb_enabled and self._table:
            try:
                ttl_timestamp = int(time.time()) + 86400
                item = {
                    "pk": f"SESSION#{session_id}",
                    "sk": "INSPECTION",
                    "type": "link_inspection",
                    "data": json.dumps(inspection_dict),
                    "ttl": ttl_timestamp
                }
                self._table.put_item(Item=item)
            except Exception as e:
                print(f"[SESSION STORE] DynamoDB save_inspection failed: {e}")

    async def get_inspection(self, session_id: str) -> Optional[LinkInspectionResult]:
        if self._dynamodb_enabled and self._table:
            try:
                response = self._table.get_item(
                    Key={"pk": f"SESSION#{session_id}", "sk": "INSPECTION"}
                )
                item = response.get("Item")
                if item and "data" in item:
                    return LinkInspectionResult.model_validate(json.loads(item["data"]))
            except Exception as e:
                print(f"[SESSION STORE] DynamoDB get_inspection failed: {e}")

        mem_data = self._memory_inspections.get(session_id)
        if mem_data:
            return LinkInspectionResult.model_validate(mem_data)
        return None

session_store = SessionStore()
