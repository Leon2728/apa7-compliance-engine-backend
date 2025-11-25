"""Tests for CoachService DETECT_PROFILE mode."""

import json
import pytest
from unittest.mock import MagicMock, patch
from api.models.coach import CoachRequest, CoachMode, CoachResponse
from api.models.profile_models import DocumentProfileAnalysis
from api.services.coach_service import CoachService


class TestCoachServiceDetectProfile:
    """Test suite for DETECT_PROFILE mode in CoachService."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return MagicMock()

    @pytest.fixture
    def coach_service_with_llm(self, mock_llm_client):
        """Create a CoachService instance with mocked LLM."""
        service = CoachService(llm_client=mock_llm_client)
        return service

    @pytest.fixture
    def coach_service_without_llm(self):
        """Create a CoachService instance without LLM."""
        service = CoachService(llm_client=None)
        return service

    @pytest.fixture
    def valid_profile_json(self):
        """Return a valid profile analysis JSON response."""
        return {
            "main_elements": ["abstract", "introduction", "methodology"],
            "found_elements": ["abstract", "introduction"],
            "missing_elements": ["methodology"],
            "formatting_issues": ["Missing page numbers in header"],
            "compliance_score": 0.75,
            "recommendations": ["Add page numbers to header"]
        }

    @pytest.fixture
    def detect_profile_request(self, valid_profile_json):
        """Create a valid DETECT_PROFILE request."""
        return CoachRequest(
            mode=CoachMode.DETECT_PROFILE,
            document_text="Este es un documento de prueba.",
            context="test_context"
        )

    def test_detect_profile_with_valid_llm_response(self, coach_service_with_llm, detect_profile_request, valid_profile_json):
        """Test DETECT_PROFILE with valid LLM response."""
        # Mock LLM response
        coach_service_with_llm.llm_client.generate = MagicMock(
            return_value=json.dumps(valid_profile_json)
        )

        # Execute
        response = coach_service_with_llm.handle(detect_profile_request)

        # Assert
        assert response is not None
        assert response.mode == CoachMode.DETECT_PROFILE
        assert response.profile_analysis is not None
        assert response.profile_analysis.compliance_score == 0.75

    def test_detect_profile_with_missing_document_text(self, coach_service_with_llm):
        """Test DETECT_PROFILE request with missing document_text."""
        # Create request without document_text
        request = CoachRequest(
            mode=CoachMode.DETECT_PROFILE,
            context="test_context"
        )

        # Execute and Assert
        response = coach_service_with_llm.handle(request)
        assert response is not None
        # Should handle gracefully - either error response or default

    def test_detect_profile_without_llm_client(self, coach_service_without_llm, detect_profile_request):
        """Test DETECT_PROFILE fallback when LLM client is unavailable."""
        # Execute
        response = coach_service_without_llm.handle(detect_profile_request)

        # Assert - should return valid response even without LLM
        assert response is not None
        assert response.mode == CoachMode.DETECT_PROFILE
        # Fallback behavior should be graceful

    def test_detect_profile_parses_json_correctly(self, coach_service_with_llm, detect_profile_request, valid_profile_json):
        """Test that JSON response is parsed correctly into DocumentProfileAnalysis."""
        coach_service_with_llm.llm_client.generate = MagicMock(
            return_value=json.dumps(valid_profile_json)
        )

        # Execute
        response = coach_service_with_llm.handle(detect_profile_request)

        # Assert
        assert isinstance(response.profile_analysis, DocumentProfileAnalysis)
        assert response.profile_analysis.found_elements == ["abstract", "introduction"]
        assert response.profile_analysis.missing_elements == ["methodology"]

    def test_detect_profile_handles_invalid_json(self, coach_service_with_llm, detect_profile_request):
        """Test handling of invalid JSON from LLM."""
        coach_service_with_llm.llm_client.generate = MagicMock(
            return_value="Invalid JSON response"
        )

        # Execute
        response = coach_service_with_llm.handle(detect_profile_request)

        # Assert - should handle gracefully
        assert response is not None
        assert response.mode == CoachMode.DETECT_PROFILE
