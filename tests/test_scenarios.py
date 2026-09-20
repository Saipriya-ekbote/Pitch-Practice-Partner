"""
Comprehensive test suite for Pitch Practice Partner.
Covers Phase 1 (Baseline), Phase 2 (Persona Engine), Phase 3 (Conversation Engine),
and Phase 4 (Conversation Intelligence & Evidence Analysis).
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.scenarios.scenario_models import (
    Scenario,
    Persona,
    PRACTICE_MODES,
    DIFFICULTY_LEVELS,
)
from src.scenarios.scenario_manager import ScenarioManager
from src.conversation.conversation_models import (
    ConversationMessage,
    PracticeSession,
    MessageRole,
    SessionStatus,
)
from src.conversation.conversation_manager import ConversationManager
from src.ai.provider import DemoProvider, RealAIProvider, get_ai_provider
from src.intelligence.analysis_models import (
    ConversationAnalysis,
    ResponseFeature,
    QuestionEvidence,
    ConcernEvidence,
    ObjectionEvidence,
)
from src.intelligence.detectors import (
    extract_response_features,
    detect_filler_words,
    detect_repetitions,
    extract_questions_from_text,
    assess_question_alignment,
    detect_potential_contradictions,
)
from src.intelligence.conversation_analyzer import (
    ConversationAnalyzer,
    HRInterviewStrategy,
    TechnicalInterviewStrategy,
    ClientPitchStrategy,
    ProjectVivaStrategy,
    GroupDiscussionStrategy,
    ManagerialInterviewStrategy,
)
from src.evaluation.evaluation_models import (
    EvaluationResult,
    ScoreDimension,
    ModeEvaluation,
    DimensionStatus,
)
from src.evaluation.scoring_rules import (
    calculate_question_handling_score,
    calculate_topic_coverage_score,
    calculate_communication_score,
    calculate_relevance_score,
    calculate_objection_handling_score,
)
from src.evaluation.mode_evaluators import (
    BaseModeEvaluator,
    HRInterviewEvaluator,
    TechnicalInterviewEvaluator,
    ClientPitchEvaluator,
    ProjectVivaEvaluator,
    GroupDiscussionEvaluator,
    ManagerialInterviewEvaluator,
    MODE_EVALUATOR_REGISTRY,
)
from src.evaluation.evaluation_engine import EvaluationEngine



# ==============================================================================
# Phase 1: Scenario Model Tests (Preserved Baseline)
# ==============================================================================

def test_scenario_creation_valid():
    """Verify that a valid Scenario can be created with expected attributes."""
    scenario = Scenario(
        id="test_01",
        name="Test Scenario",
        mode="HR Interview",
        description="A test scenario description.",
        difficulty="Beginner",
        persona="Lead Recruiter",
        objective="Test objective.",
        expected_topics=["Topic A", "Topic B"],
        opening_message="Hello, ready for the test?",
        max_turns=4,
    )
    assert scenario.id == "test_01"
    assert scenario.name == "Test Scenario"
    assert scenario.mode == "HR Interview"
    assert scenario.description == "A test scenario description."
    assert scenario.difficulty == "Beginner"
    assert scenario.persona == "Lead Recruiter"
    assert scenario.objective == "Test objective."
    assert scenario.expected_topics == ["Topic A", "Topic B"]
    assert scenario.opening_message == "Hello, ready for the test?"
    assert scenario.max_turns == 4


def test_scenario_validation_empty_id():
    """Verify ValueError is raised if scenario id is empty."""
    with pytest.raises(ValueError, match="id"):
        Scenario(
            id="",
            name="Test",
            mode="HR Interview",
            description="Desc",
            difficulty="Beginner",
        )


def test_scenario_validation_empty_name():
    """Verify ValueError is raised if scenario name is empty."""
    with pytest.raises(ValueError, match="name"):
        Scenario(
            id="test_02",
            name="",
            mode="HR Interview",
            description="Desc",
            difficulty="Beginner",
        )


def test_scenario_validation_invalid_mode():
    """Verify ValueError is raised if mode is not in PRACTICE_MODES."""
    with pytest.raises(ValueError, match="Invalid scenario mode"):
        Scenario(
            id="test_03",
            name="Test Name",
            mode="Unknown Mode",
            description="Desc",
            difficulty="Beginner",
        )


def test_scenario_validation_invalid_difficulty():
    """Verify ValueError is raised if difficulty is not in DIFFICULTY_LEVELS."""
    with pytest.raises(ValueError, match="Invalid scenario difficulty"):
        Scenario(
            id="test_04",
            name="Test Name",
            mode="Technical Interview",
            description="Desc",
            difficulty="SuperHard",
        )


def test_scenario_serialization_roundtrip():
    """Verify from_dict and to_dict methods serialize correctly."""
    data = {
        "id": "tech_01",
        "name": "Python Clean Code",
        "mode": "Technical Interview",
        "description": "Explaining clean architecture.",
        "difficulty": "Intermediate",
        "persona": "Senior Architect",
        "objective": "Articulate clean design.",
        "expected_topics": ["SOLID", "DRY"],
        "opening_message": "Tell me about SOLID principles.",
        "max_turns": 5,
    }
    scenario = Scenario.from_dict(data)
    assert scenario.id == data["id"]
    assert scenario.expected_topics == ["SOLID", "DRY"]
    assert scenario.to_dict()["id"] == data["id"]
    assert scenario.to_dict()["name"] == data["name"]


# ==============================================================================
# Phase 1: ScenarioManager Tests (Preserved Baseline)
# ==============================================================================

def test_scenario_manager_default_load():
    """Verify ScenarioManager loads default bundled sample scenarios."""
    manager = ScenarioManager()
    scenarios = manager.get_all_scenarios()
    assert len(scenarios) > 0

    modes_in_data = {s.mode for s in scenarios}
    for mode in PRACTICE_MODES:
        assert mode in modes_in_data, f"Missing mode in default data: {mode}"


def test_scenario_manager_get_by_mode():
    """Verify filtering scenarios by mode works as expected."""
    manager = ScenarioManager()
    hr_scenarios = manager.get_scenarios_by_mode("HR Interview")
    assert len(hr_scenarios) > 0
    assert all(s.mode == "HR Interview" for s in hr_scenarios)

    hr_scenarios_case = manager.get_scenarios_by_mode("  hr interview  ")
    assert len(hr_scenarios_case) == len(hr_scenarios)


def test_scenario_manager_get_by_invalid_mode():
    """Verify filtering by invalid or unknown mode returns an empty list."""
    manager = ScenarioManager()
    assert manager.get_scenarios_by_mode("NonExistentMode") == []
    assert manager.get_scenarios_by_mode("") == []
    assert manager.get_scenarios_by_mode(None) == []  # type: ignore


def test_scenario_manager_get_by_id_valid():
    """Verify retrieving a scenario by existing ID."""
    manager = ScenarioManager()
    scenario = manager.get_scenario_by_id("hr_intro_01")
    assert scenario is not None
    assert scenario.id == "hr_intro_01"
    assert scenario.mode == "HR Interview"


def test_scenario_manager_get_by_id_invalid():
    """Verify retrieving by unknown or invalid ID returns None."""
    manager = ScenarioManager()
    assert manager.get_scenario_by_id("non_existent_id") is None
    assert manager.get_scenario_by_id("") is None
    assert manager.get_scenario_by_id(None) is None  # type: ignore


def test_scenario_manager_get_by_difficulty():
    """Verify filtering by difficulty level."""
    manager = ScenarioManager()
    beginner_scenarios = manager.get_scenarios_by_difficulty("Beginner")
    assert len(beginner_scenarios) > 0
    assert all(s.difficulty == "Beginner" for s in beginner_scenarios)

    assert manager.get_scenarios_by_difficulty("InvalidDifficulty") == []
    assert manager.get_scenarios_by_difficulty("") == []


def test_scenario_manager_modes_and_difficulties():
    """Verify helper methods for modes and difficulties."""
    manager = ScenarioManager()
    assert manager.get_modes() == PRACTICE_MODES
    assert manager.get_difficulties() == DIFFICULTY_LEVELS


def test_scenario_manager_custom_path_missing():
    """Verify graceful handling when data path does not exist."""
    manager = ScenarioManager(data_path="non_existent_directory/file.json")
    assert manager.get_all_scenarios() == []
    assert manager.get_scenarios_by_mode("HR Interview") == []
    assert manager.get_scenario_by_id("any_id") is None


def test_scenario_manager_custom_path_corrupted_json():
    """Verify graceful handling when JSON is corrupted or invalid."""
    with TemporaryDirectory() as tmp_dir:
        bad_json_file = Path(tmp_dir) / "corrupt.json"
        bad_json_file.write_text("{ this is not valid json }", encoding="utf-8")

        manager = ScenarioManager(data_path=bad_json_file)
        assert manager.get_all_scenarios() == []


def test_scenario_manager_custom_path_invalid_structure():
    """Verify graceful handling when JSON is not a list of scenario objects."""
    with TemporaryDirectory() as tmp_dir:
        obj_json_file = Path(tmp_dir) / "dict_instead_of_list.json"
        obj_json_file.write_text('{"key": "value"}', encoding="utf-8")

        manager = ScenarioManager(data_path=obj_json_file)
        assert manager.get_all_scenarios() == []


def test_scenario_manager_directory_loading():
    """Verify loading from a directory with multiple JSON files."""
    with TemporaryDirectory() as tmp_dir:
        file1 = Path(tmp_dir) / "mode1.json"
        file2 = Path(tmp_dir) / "mode2.json"

        item1 = [
            {
                "id": "dir_01",
                "name": "Dir Scenario 1",
                "mode": "HR Interview",
                "description": "Desc 1",
                "difficulty": "Beginner",
            }
        ]
        item2 = [
            {
                "id": "dir_02",
                "name": "Dir Scenario 2",
                "mode": "Client Pitch",
                "description": "Desc 2",
                "difficulty": "Advanced",
            }
        ]

        file1.write_text(json.dumps(item1), encoding="utf-8")
        file2.write_text(json.dumps(item2), encoding="utf-8")

        manager = ScenarioManager(data_path=tmp_dir)
        scenarios = manager.get_all_scenarios()
        assert len(scenarios) == 2
        assert manager.get_scenario_by_id("dir_01") is not None
        assert manager.get_scenario_by_id("dir_02") is not None


# ==============================================================================
# Phase 1: AI Provider & Demo Mode Tests (Preserved Baseline)
# ==============================================================================

def test_demo_provider_status():
    """Verify DemoProvider reports Demo Mode and not connected status."""
    provider = DemoProvider()
    status = provider.get_status()
    assert status.is_demo is True
    assert status.is_connected is False
    assert "Demo Mode" in status.name


def test_demo_provider_response():
    """Verify DemoProvider returns deterministic placeholder response."""
    provider = DemoProvider()
    response = provider.generate_response("Hello")
    assert "[DEMO MODE]" in response


def test_get_ai_provider_factory():
    """Verify factory returns DemoProvider in Phase 1/2 without keys."""
    provider = get_ai_provider()
    assert isinstance(provider, (DemoProvider, RealAIProvider))


# ==============================================================================
# Phase 2: Persona Model Tests
# ==============================================================================

def test_persona_creation_valid():
    """Verify that a valid Persona can be created with all attributes."""
    persona = Persona(
        id="persona_cto_01",
        name="Skeptical CTO",
        role="Chief Technology Officer",
        personality="Analytical, demanding",
        background="Veteran engineering executive.",
        objective="Validate technical scalability and ROI.",
        knowledge_level="Enterprise Architecture",
        communication_style="Direct, concise",
        concerns=["Security", "Cost", "Scalability"],
        behaviors=["Challenges claims", "Asks for benchmarks"],
        objection_types=["Compliance risks", "Migration overhead"],
        follow_up_strategy="Drill into architecture failure points.",
        difficulty="Advanced",
        supported_modes=["Client Pitch"],
    )
    assert persona.id == "persona_cto_01"
    assert persona.name == "Skeptical CTO"
    assert persona.role == "Chief Technology Officer"
    assert persona.difficulty == "Advanced"
    assert "Security" in persona.concerns
    assert "Challenges claims" in persona.behaviors
    assert "Compliance risks" in persona.objection_types
    assert persona.supported_modes == ["Client Pitch"]


def test_persona_validation_empty_id():
    """Verify ValueError is raised if persona ID is empty."""
    with pytest.raises(ValueError, match="id"):
        Persona(
            id="",
            name="Name",
            role="Role",
            personality="P",
            background="B",
            objective="O",
            knowledge_level="K",
            communication_style="C",
            difficulty="Beginner",
        )


def test_persona_validation_empty_name():
    """Verify ValueError is raised if persona name is empty."""
    with pytest.raises(ValueError, match="name"):
        Persona(
            id="p_01",
            name="",
            role="Role",
            personality="P",
            background="B",
            objective="O",
            knowledge_level="K",
            communication_style="C",
            difficulty="Beginner",
        )


def test_persona_validation_empty_role():
    """Verify ValueError is raised if persona role is empty."""
    with pytest.raises(ValueError, match="role"):
        Persona(
            id="p_01",
            name="Name",
            role="",
            personality="P",
            background="B",
            objective="O",
            knowledge_level="K",
            communication_style="C",
            difficulty="Beginner",
        )


def test_persona_validation_invalid_difficulty():
    """Verify ValueError is raised if persona difficulty is invalid."""
    with pytest.raises(ValueError, match="Invalid persona difficulty"):
        Persona(
            id="p_01",
            name="Name",
            role="Role",
            personality="P",
            background="B",
            objective="O",
            knowledge_level="K",
            communication_style="C",
            difficulty="Nightmare",
        )


def test_persona_serialization_roundtrip():
    """Verify Persona from_dict and to_dict methods serialize and deserialize cleanly."""
    data = {
        "id": "persona_recruiter_01",
        "name": "Friendly Recruiter",
        "role": "Recruiting Specialist",
        "personality": "Warm, engaging",
        "background": "HR professional with 5 years experience.",
        "objective": "Assess team culture fit.",
        "knowledge_level": "Corporate HR",
        "communication_style": "Supportive",
        "concerns": ["Cultural alignment", "Career motivation"],
        "behaviors": ["Nods encouragingly", "Asks open questions"],
        "objection_types": ["Vague career goals"],
        "follow_up_strategy": "Ask for specific project highlights.",
        "difficulty": "Beginner",
        "supported_modes": ["HR Interview"],
    }
    persona = Persona.from_dict(data)
    assert persona.id == data["id"]
    assert persona.concerns == data["concerns"]
    assert persona.to_dict() == data


# ==============================================================================
# Phase 2: Extended Scenario Model Tests
# ==============================================================================

def test_scenario_extended_fields():
    """Verify Scenario handles Phase 2 fields like persona_id and forbidden_topics."""
    scenario = Scenario(
        id="scenario_p2_01",
        name="Advanced System Pitch",
        mode="Client Pitch",
        description="Pitching high availability systems.",
        difficulty="Advanced",
        persona_id="persona_cto_01",
        conversation_goal="Convince CTO to adopt new cache cluster.",
        expected_topics=["Latency", "Throughput", "SLA"],
        forbidden_topics=["Unrealistic 100% uptime claims"],
        opening_message="What guarantees do you offer?",
        max_turns=6,
    )
    assert scenario.persona_id == "persona_cto_01"
    assert scenario.conversation_goal == "Convince CTO to adopt new cache cluster."
    assert scenario.objective == "Convince CTO to adopt new cache cluster."
    assert scenario.forbidden_topics == ["Unrealistic 100% uptime claims"]
    assert scenario.maximum_turns == 6


def test_scenario_extended_serialization():
    """Verify extended Scenario model serializes all fields for Phase 2."""
    data = {
        "id": "scenario_p2_02",
        "name": "Viva Defense",
        "mode": "Project Viva",
        "description": "Defending ML methodology.",
        "difficulty": "Advanced",
        "persona_id": "persona_viva_examiner",
        "conversation_goal": "Defend dataset validation and error metrics.",
        "expected_topics": ["Validation split", "F1 score"],
        "forbidden_topics": ["Evaluating on training data"],
        "opening_message": "How did you validate your dataset?",
        "max_turns": 5,
        "maximum_turns": 5,
    }
    scenario = Scenario.from_dict(data)
    assert scenario.persona_id == "persona_viva_examiner"
    assert scenario.forbidden_topics == ["Evaluating on training data"]
    dict_out = scenario.to_dict()
    assert dict_out["persona_id"] == "persona_viva_examiner"
    assert dict_out["forbidden_topics"] == ["Evaluating on training data"]
    assert dict_out["conversation_goal"] == "Defend dataset validation and error metrics."


# ==============================================================================
# Phase 2: ScenarioManager Persona Queries & Relationships
# ==============================================================================

def test_scenario_manager_loads_all_personas():
    """Verify ScenarioManager loads all bundled personas."""
    manager = ScenarioManager()
    personas = manager.get_all_personas()
    assert len(personas) >= 10

    persona_ids = {p.id for p in personas}
    expected_ids = [
        "persona_hr_friendly",
        "persona_hr_strict",
        "persona_tech_peer",
        "persona_tech_senior",
        "persona_pitch_cto",
        "persona_pitch_manager",
        "persona_pitch_exec",
        "persona_viva_professor",
        "persona_viva_examiner",
        "persona_gd_confident",
        "persona_gd_analytical",
        "persona_mgr_lead",
    ]
    for pid in expected_ids:
        assert pid in persona_ids, f"Expected persona '{pid}' missing from persona library."


def test_scenario_manager_get_persona_by_id():
    """Verify looking up persona by valid and invalid ID."""
    manager = ScenarioManager()
    persona = manager.get_persona_by_id("persona_pitch_cto")
    assert persona is not None
    assert persona.name == "Skeptical CTO"
    assert persona.role == "Chief Technology Officer"
    assert persona.difficulty == "Advanced"

    assert manager.get_persona_by_id("invalid_persona_id") is None
    assert manager.get_persona_by_id("") is None
    assert manager.get_persona_by_id(None) is None  # type: ignore


def test_scenario_manager_get_personas_by_mode():
    """Verify filtering personas by supported practice mode."""
    manager = ScenarioManager()
    pitch_personas = manager.get_personas_by_mode("Client Pitch")
    assert len(pitch_personas) >= 3
    for p in pitch_personas:
        assert any(m.lower() == "client pitch" for m in p.supported_modes)

    assert manager.get_personas_by_mode("UnknownMode") == []
    assert manager.get_personas_by_mode("") == []
    assert manager.get_personas_by_mode(None) == []  # type: ignore


def test_scenario_manager_get_persona_for_scenario():
    """Verify retrieving associated Persona for a given scenario."""
    manager = ScenarioManager()
    persona = manager.get_persona_for_scenario("hr_intro_01")
    assert persona is not None
    assert persona.id == "persona_hr_friendly"
    assert persona.name == "Friendly HR Recruiter"

    persona_tech = manager.get_persona_for_scenario("tech_system_design_02")
    assert persona_tech is not None
    assert persona_tech.id == "persona_tech_senior"

    assert manager.get_persona_for_scenario("non_existent_scenario") is None
    assert manager.get_persona_for_scenario("") is None


def test_scenario_manager_get_scenarios_with_personas():
    """Verify get_scenarios_with_personas pairs each scenario with its Persona."""
    manager = ScenarioManager()
    paired = manager.get_scenarios_with_personas()
    assert len(paired) > 0
    for item in paired:
        assert "scenario" in item
        assert "persona" in item
        assert isinstance(item["scenario"], Scenario)
        if item["scenario"].persona_id:
            assert item["persona"] is not None
            assert item["persona"].id == item["scenario"].persona_id


def test_scenario_manager_custom_persona_path_corrupted():
    """Verify ScenarioManager handles corrupted personas file gracefully."""
    with TemporaryDirectory() as tmp_dir:
        bad_json = Path(tmp_dir) / "bad_personas.json"
        bad_json.write_text("{ not json", encoding="utf-8")

        manager = ScenarioManager(personas_path=bad_json)
        assert manager.get_all_personas() == []
        assert manager.get_persona_by_id("any") is None


def test_scenario_manager_custom_persona_directory_loading():
    """Verify ScenarioManager loads personas across multiple JSON files in a directory."""
    with TemporaryDirectory() as tmp_dir:
        p1_file = Path(tmp_dir) / "p1.json"
        p2_file = Path(tmp_dir) / "p2.json"

        p1_data = [
            {
                "id": "dir_p1",
                "name": "Persona Dir 1",
                "role": "Role 1",
                "personality": "P1",
                "background": "B1",
                "objective": "O1",
                "knowledge_level": "K1",
                "communication_style": "C1",
                "difficulty": "Beginner",
                "supported_modes": ["HR Interview"],
            }
        ]
        p2_data = [
            {
                "id": "dir_p2",
                "name": "Persona Dir 2",
                "role": "Role 2",
                "personality": "P2",
                "background": "B2",
                "objective": "O2",
                "knowledge_level": "K2",
                "communication_style": "C2",
                "difficulty": "Advanced",
                "supported_modes": ["Client Pitch"],
            }
        ]

        p1_file.write_text(json.dumps(p1_data), encoding="utf-8")
        p2_file.write_text(json.dumps(p2_data), encoding="utf-8")

        manager = ScenarioManager(personas_path=tmp_dir)
        assert len(manager.get_all_personas()) == 2
        assert manager.get_persona_by_id("dir_p1") is not None
        assert manager.get_persona_by_id("dir_p2") is not None


# ==============================================================================
# Phase 2: Data Integrity Tests
# ==============================================================================

def test_data_integrity_all_scenarios_reference_valid_personas():
    """Verify every bundled scenario has a valid, existing persona reference."""
    manager = ScenarioManager()
    scenarios = manager.get_all_scenarios()
    assert len(scenarios) > 0

    for scenario in scenarios:
        assert scenario.persona_id != "", f"Scenario '{scenario.id}' has an empty persona_id."
        persona = manager.get_persona_by_id(scenario.persona_id)
        assert persona is not None, f"Scenario '{scenario.id}' references non-existent persona '{scenario.persona_id}'."


def test_data_integrity_all_personas_have_valid_fields():
    """Verify all bundled personas satisfy required non-empty lists and descriptors."""
    manager = ScenarioManager()
    personas = manager.get_all_personas()
    assert len(personas) > 0

    for persona in personas:
        assert persona.id.strip() != ""
        assert persona.name.strip() != ""
        assert persona.role.strip() != ""
        assert persona.personality.strip() != ""
        assert persona.objective.strip() != ""
        assert persona.communication_style.strip() != ""
        assert len(persona.concerns) > 0, f"Persona '{persona.id}' has empty concerns."
        assert len(persona.behaviors) > 0, f"Persona '{persona.id}' has empty behaviors."
        assert persona.difficulty in DIFFICULTY_LEVELS


def test_data_integrity_all_six_modes_covered_by_personas():
    """Verify that each of the 6 practice modes has corresponding personas."""
    manager = ScenarioManager()
    for mode in PRACTICE_MODES:
        personas = manager.get_personas_by_mode(mode)
        assert len(personas) > 0, f"Practice mode '{mode}' has no associated personas."


# ==============================================================================
# Phase 3: Conversation Models & Session Tests
# ==============================================================================

def test_conversation_message_creation_valid():
    """Verify creating a valid ConversationMessage."""
    msg = ConversationMessage(role=MessageRole.USER.value, content="Hello interviewer!")
    assert msg.role == "user"
    assert msg.content == "Hello interviewer!"
    assert msg.timestamp is not None


def test_conversation_message_validation_invalid_role():
    """Verify ValueError is raised if role is invalid."""
    with pytest.raises(ValueError, match="role"):
        ConversationMessage(role="invalid_role", content="Content")


def test_conversation_message_validation_empty_content():
    """Verify ValueError is raised if content is empty."""
    with pytest.raises(ValueError, match="content"):
        ConversationMessage(role=MessageRole.USER.value, content="")


def test_conversation_message_serialization():
    """Verify ConversationMessage to_dict and from_dict roundtrip."""
    data = {"role": "assistant", "content": "Tell me about your background.", "timestamp": "2026-09-20T10:00:00"}
    msg = ConversationMessage.from_dict(data)
    assert msg.role == "assistant"
    assert msg.content == data["content"]
    assert msg.to_dict() == data


def test_practice_session_lifecycle_methods():
    """Verify PracticeSession status checks and helper methods."""
    session = PracticeSession(
        scenario_id="hr_01",
        persona_id="persona_hr",
        mode="HR Interview",
        max_turns=3,
        status=SessionStatus.ACTIVE.value,
    )
    assert session.is_active() is True
    assert session.is_completed() is False

    session.add_message("assistant", "Opening question")
    assert len(session.conversation_history) == 1

    session.turn_number = 3
    assert session.is_completed() is True
    assert session.is_active() is False


def test_practice_session_serialization():
    """Verify PracticeSession roundtrip serialization."""
    session = PracticeSession(
        scenario_id="pitch_01",
        persona_id="persona_cto",
        mode="Client Pitch",
        difficulty="Advanced",
        max_turns=4,
        status=SessionStatus.ACTIVE.value,
    )
    session.add_message("assistant", "Opening prompt")
    session.add_message("user", "Candidate response")
    serialized = session.to_dict()

    restored = PracticeSession.from_dict(serialized)
    assert restored.session_id == session.session_id
    assert restored.scenario_id == session.scenario_id
    assert len(restored.conversation_history) == 2
    assert restored.conversation_history[1].content == "Candidate response"


# ==============================================================================
# Phase 3: ConversationManager & Multi-Turn Role-Play Tests
# ==============================================================================

def test_conversation_manager_start_session():
    """Verify starting a session initializes history with scenario opening message."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("hr_intro_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona, difficulty="Beginner")

    assert session.status == SessionStatus.ACTIVE.value
    assert session.turn_number == 0
    assert len(session.conversation_history) == 1
    assert session.conversation_history[0].role == MessageRole.ASSISTANT.value
    assert session.conversation_history[0].content == scenario.opening_message


def test_conversation_manager_send_user_message_turn_flow():
    """Verify submitting a user answer increments turn number and returns AI follow-up."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("tech_python_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona)

    updated_session, assistant_msg = conv_mgr.send_user_message(
        session=session,
        user_content="I would use a min-heap data structure to keep the top K items in O(N log K) time.",
        scenario=scenario,
        persona=persona,
    )

    assert updated_session.turn_number == 1
    assert len(updated_session.conversation_history) == 3
    assert updated_session.conversation_history[1].role == "user"
    assert updated_session.conversation_history[2].role == "assistant"
    assert assistant_msg.content == updated_session.conversation_history[2].content
    assert "[DEMO MODE]" in assistant_msg.content


def test_conversation_manager_empty_user_message_error():
    """Verify sending an empty user message raises ValueError."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("hr_intro_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona)

    with pytest.raises(ValueError, match="empty"):
        conv_mgr.send_user_message(session, "", scenario, persona)

    with pytest.raises(ValueError, match="empty"):
        conv_mgr.send_user_message(session, "   ", scenario, persona)


def test_conversation_manager_max_turns_termination():
    """Verify reaching maximum turns automatically completes the session."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("pitch_ai_solution_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona)
    session.max_turns = 2

    conv_mgr.send_user_message(session, "Our ML pipeline guarantees 99.9% uptime and low latency.", scenario, persona)
    assert session.is_active() is True

    conv_mgr.send_user_message(session, "We adhere strictly to SOC-2 and HIPAA compliance standards.", scenario, persona)
    assert session.turn_number == 2
    assert session.is_completed() is True
    assert session.status == SessionStatus.COMPLETED.value
    assert session.ended_at is not None

    with pytest.raises(ValueError, match="Cannot send message"):
        conv_mgr.send_user_message(session, "Another response", scenario, persona)


def test_conversation_manager_end_and_restart_session():
    """Verify explicitly ending and restarting sessions ensures complete state isolation."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("viva_arch_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session1 = conv_mgr.start_session(scenario, persona)
    conv_mgr.send_user_message(session1, "I chose PostgreSQL for relational ACID transactions.", scenario, persona)

    ended_session = conv_mgr.end_session(session1)
    assert ended_session.status == SessionStatus.COMPLETED.value
    assert ended_session.ended_at is not None

    session2 = conv_mgr.restart_session(scenario, persona)
    assert session2.session_id != session1.session_id
    assert session2.turn_number == 0
    assert len(session2.conversation_history) == 1
    assert session2.status == SessionStatus.ACTIVE.value


def test_demo_provider_dynamic_responses_for_distinct_inputs():
    """Verify that DemoProvider returns distinct contextual follow-ups when given different answers."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("pitch_ai_solution_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)
    conv_mgr = ConversationManager()

    session_a = conv_mgr.start_session(scenario, persona)
    _, msg_a = conv_mgr.send_user_message(
        session_a,
        "Our solution saves budget and reduces operational licensing cost by 40% with high ROI.",
        scenario,
        persona,
    )

    session_b = conv_mgr.start_session(scenario, persona)
    _, msg_b = conv_mgr.send_user_message(
        session_b,
        "We prioritize enterprise data privacy and GDPR compliance with end-to-end encryption.",
        scenario,
        persona,
    )

    assert msg_a.content != msg_b.content
    assert "budget" in msg_a.content.lower() or "cost" in msg_a.content.lower() or "payback" in msg_a.content.lower()
    assert "security" in msg_b.content.lower() or "privacy" in msg_b.content.lower() or "compliance" in msg_b.content.lower()


def test_demo_provider_brief_answer_handling():
    """Verify DemoProvider prods for more detail when answer is overly brief."""
    provider = DemoProvider()
    response = provider.generate_roleplay_response(
        system_prompt="",
        conversation_history=[],
        user_message="Yes.",
        scenario_context={"persona_name": "Skeptical CTO", "persona_role": "Chief Technology Officer"},
    )
    assert "brief" in response.lower() or "elaborate" in response.lower()


def test_real_ai_provider_fallback_without_key():
    """Verify RealAIProvider falls back gracefully to DemoProvider when unconfigured."""
    provider = RealAIProvider(api_key="", provider_name="openai")
    status = provider.get_status()
    assert status.is_connected is False
    assert status.is_demo is True

    response = provider.generate_roleplay_response(
        system_prompt="Test system prompt",
        conversation_history=[],
        user_message="Our distributed architecture uses Redis cluster.",
        scenario_context={"persona_name": "Examiner", "difficulty": "Advanced"},
    )
    assert "[DEMO MODE]" in response


# ==============================================================================
# Phase 4: Linguistic Feature & Detector Tests
# ==============================================================================

def test_extract_response_features_thresholds():
    """Verify word count, sentence count, and length categorization thresholds."""
    # Short (< 20 words)
    f_short = extract_response_features(1, "I built a machine learning model.")
    assert f_short.word_count == 6
    assert f_short.sentence_count == 1
    assert f_short.length_category == "short"

    # Medium (20 to 60 words)
    med_text = (
        "In my previous company, I was tasked with migrating our database to PostgreSQL. "
        "I analyzed query patterns, designed the schema indexing strategy, and coordinated "
        "with our engineering team to complete migration with zero downtime."
    )
    f_med = extract_response_features(2, med_text)
    assert 20 <= f_med.word_count <= 60
    assert f_med.length_category == "medium"
    assert f_med.sentence_count == 2
    assert f_med.avg_sentence_length > 0

    # Long (> 60 words)
    long_text = " ".join(["word"] * 65) + "."
    f_long = extract_response_features(3, long_text)
    assert f_long.word_count == 65
    assert f_long.length_category == "long"


def test_detect_filler_words_contextual():
    """Verify filler detection accurately identifies vocal hesitations without false positives on legitimate words."""
    # Unconditional filler 'um' and 'uh'
    t1 = "Um, I built a model, uh, for text classification."
    f1 = detect_filler_words(t1)
    assert f1.get("um") == 1
    assert f1.get("uh") == 1

    # Legitimate use of 'like' (should NOT be detected as a filler)
    t2 = "I like Python and I like writing clean code."
    f2 = detect_filler_words(t2)
    assert "like" not in f2

    # Contextual filler 'like' (surrounded by pauses/commas)
    t3 = "It was, like, really hard to scale."
    f3 = detect_filler_words(t3)
    assert f3.get("like") == 1

    # Multi-word filler 'you know'
    t4 = "We had to pivot quickly, you know, because of deadlines."
    f4 = detect_filler_words(t4)
    assert f4.get("you know") == 1


def test_detect_repetitions_filtering():
    """Verify repetition detector finds repeated non-stop phrases and words."""
    texts = [
        "We implemented data security protocols to protect sensitive customer data.",
        "Our data security team prioritized strict encryption standards.",
        "We ensure data security at every layer of the infrastructure.",
    ]
    phrases, words = detect_repetitions(texts)
    
    phrase_names = [p["phrase"] for p in phrases]
    assert any("data security" in p for p in phrase_names)

    word_names = [w["word"] for w in words]
    assert "the" not in word_names
    assert "and" not in word_names


def test_extract_questions_from_text():
    """Verify question extraction detects interrogatives and question marks."""
    ai_text = "Welcome to the interview! How would you design a distributed cache? Tell me about your approach."
    questions = extract_questions_from_text(ai_text)
    assert len(questions) >= 2
    assert any("distributed cache" in q for q in questions)


def test_assess_question_alignment_heuristic():
    """Verify alignment heuristic distinguishes addressed vs unaddressed answers."""
    q = "How do you handle security and compliance?"
    
    # Addressed response
    ans_good = "We enforce SOC-2 compliance and end-to-end security encryption for all data."
    assert assess_question_alignment(q, ans_good) == "addressed"

    # Unaddressed response
    ans_bad = "No."
    assert assess_question_alignment(q, ans_bad) == "unaddressed"


def test_detect_potential_contradictions():
    """Verify contradiction detector flags obvious opposing technical claims."""
    turns = [
        "Our backend operates in real-time stream processing mode.",
        "We batch all customer data and process it once every 24 hours.",
    ]
    contradictions = detect_potential_contradictions(turns)
    assert len(contradictions) >= 1
    assert "real-time" in contradictions[0].lower()


# ==============================================================================
# Phase 4: Mode-Specific Strategy Tests
# ==============================================================================

def test_hr_interview_star_strategy():
    """Verify HR interview strategy detects STAR indicators."""
    strategy = HRInterviewStrategy()
    user_texts = [
        "At my previous company, the situation was that our legacy server was crashing.",
        "My task was to rebuild the authentication pipeline within two weeks.",
        "I decided to implement OAuth2 with JWT tokens and led the migration.",
        "As a result, we reduced login latency by 50% with zero security incidents.",
    ]
    evidence = strategy.analyze(user_texts=user_texts, assistant_texts=[])
    assert evidence.mode == "HR Interview"
    star = evidence.indicators["star_components"]
    assert star["Situation"] == "detected"
    assert star["Task"] == "detected"
    assert star["Action"] == "detected"
    assert star["Result"] == "detected"
    assert evidence.indicators["specific_metrics_provided"] == "detected"


def test_technical_interview_strategy():
    """Verify Technical Interview strategy detects complexity and architecture signals."""
    strategy = TechnicalInterviewStrategy()
    user_texts = [
        "I will use a min-heap which gives O(N log K) time complexity and O(K) space complexity.",
        "For edge cases, we check for empty streams, null values, and concurrent race conditions.",
    ]
    evidence = strategy.analyze(user_texts=user_texts, assistant_texts=[])
    assert evidence.mode == "Technical Interview"
    tech = evidence.indicators["technical_concepts"]
    assert tech["Time Complexity"] == "detected"
    assert tech["Space / Memory Overhead"] == "detected"
    assert tech["Data Structures"] == "detected"
    assert tech["Edge Cases & Boundary Conditions"] == "detected"


def test_client_pitch_strategy():
    """Verify Client Pitch strategy detects ROI, security, and value proposition signals."""
    strategy = ClientPitchStrategy()
    user_texts = [
        "Our solution offers a compelling value proposition that delivers 35% ROI within 6 months.",
        "We are fully SOC-2 and GDPR compliant with 99.99% uptime SLA.",
    ]
    evidence = strategy.analyze(user_texts=user_texts, assistant_texts=[])
    assert evidence.mode == "Client Pitch"
    pitch = evidence.indicators["pitch_components"]
    assert pitch["Value Proposition"] == "detected"
    assert pitch["Cost & ROI Justification"] == "detected"
    assert pitch["Security & Compliance"] == "detected"
    assert pitch["Scalability & Performance"] == "detected"


def test_project_viva_strategy():
    """Verify Project Viva strategy detects architecture, methodology, and limitations."""
    strategy = ProjectVivaStrategy()
    user_texts = [
        "Our capstone architecture follows a modular microservices pipeline.",
        "We evaluated PostgreSQL over MongoDB because of relational consistency trade-offs.",
        "Our validation methodology used an 80/20 train-test split achieving 92% F1 score.",
        "One known limitation is the memory constraint when processing large image datasets.",
    ]
    evidence = strategy.analyze(user_texts=user_texts, assistant_texts=[])
    assert evidence.mode == "Project Viva"
    viva = evidence.indicators["viva_components"]
    assert viva["Architecture & Design Justification"] == "detected"
    assert viva["Technology Stack Rationale"] == "detected"
    assert viva["Methodology & Experimental Rigor"] == "detected"
    assert viva["Awareness of Limitations"] == "detected"


def test_group_discussion_strategy():
    """Verify Group Discussion strategy detects discussion dynamics."""
    strategy = GroupDiscussionStrategy()
    user_texts = [
        "I agree with the previous speaker and building on that point...",
        "However, on the other hand, we must consider the ethical risks of automation.",
        "In summary, finding a balance between productivity and employee wellbeing is essential.",
    ]
    evidence = strategy.analyze(user_texts=user_texts, assistant_texts=[])
    assert evidence.mode == "Group Discussion"
    gd = evidence.indicators["discussion_dynamics"]
    assert gd["Constructive Agreement / Building On Ideas"] == "detected"
    assert gd["Respectful Counter-Argument / Nuance"] == "detected"
    assert gd["Synthesis / Common Ground"] == "detected"


def test_managerial_interview_strategy():
    """Verify Managerial Interview strategy detects leadership signals."""
    strategy = ManagerialInterviewStrategy()
    user_texts = [
        "I scheduled 1-on-1 meetings with both engineers to understand their perspectives with empathy.",
        "To resolve the conflict, we used a RICE prioritization framework and aligned with stakeholders.",
        "I took full ownership of the delay and presented a transparent recovery roadmap to executives.",
    ]
    evidence = strategy.analyze(user_texts=user_texts, assistant_texts=[])
    assert evidence.mode == "Managerial Interview"
    lead = evidence.indicators["leadership_signals"]
    assert lead["Empathetic Leadership & 1-on-1 Communication"] == "detected"
    assert lead["Conflict Mediation & De-escalation"] == "detected"
    assert lead["Prioritization Frameworks"] == "detected"
    assert lead["Ownership & Accountability"] == "detected"
    assert lead["Stakeholder Transparency"] == "detected"


# ==============================================================================
# Phase 4: Central ConversationAnalyzer End-to-End Tests
# ==============================================================================

def test_conversation_analyzer_full_session_flow():
    """
    Verify complete ConversationAnalyzer execution on a multi-turn session.
    Checks deterministic counts, questions, expected topics, and read-only preservation.
    """
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("pitch_ai_solution_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona)

    # Turn 1
    conv_mgr.send_user_message(
        session,
        "Um, our AI solution delivers a clear value proposition with 40% cost reduction and high ROI.",
        scenario,
        persona,
    )
    # Turn 2
    conv_mgr.send_user_message(
        session,
        "We enforce SOC-2 security compliance, encryption at rest, and GDPR privacy standards.",
        scenario,
        persona,
    )

    conv_mgr.end_session(session)

    # Snapshot history before analysis to verify read-only behavior
    history_len_before = len(session.conversation_history)
    history_contents_before = [m.content for m in session.conversation_history]

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session, scenario, persona)

    # 1. Verify read-only non-mutation
    assert len(session.conversation_history) == history_len_before
    assert [m.content for m in session.conversation_history] == history_contents_before

    # 2. Verify analysis metrics
    assert analysis.session_id == session.session_id
    assert analysis.total_turns == 2
    assert analysis.user_message_count == 2
    assert analysis.total_user_words > 0
    assert len(analysis.response_features) == 2
    assert analysis.filler_word_counts.get("um") == 1

    # 3. Verify topical coverage
    assert "Value proposition & ROI" in analysis.covered_expected_topics or "Security & compliance" in analysis.covered_expected_topics
    assert len(analysis.questions_detected) >= 2
    assert analysis.mode_specific_analysis is not None
    assert analysis.mode_specific_analysis.mode == "Client Pitch"


def test_conversation_analyzer_empty_session_edge_case():
    """Verify analyzer handles an empty or single-message session safely without division by zero."""
    session = PracticeSession(
        scenario_id="hr_01",
        persona_id="persona_hr",
        mode="HR Interview",
        status=SessionStatus.ACTIVE.value,
    )
    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)

    assert analysis.total_turns == 0
    assert analysis.user_message_count == 0
    assert analysis.total_user_words == 0
    assert analysis.avg_words_per_response == 0.0
    assert analysis.filler_percentage == 0.0
    assert analysis.response_features == []


# ==============================================================================
# Phase 5: Test Helpers
# ==============================================================================

def _make_analysis(
    session_id: str = "test_sess",
    mode: str = "HR Interview",
    difficulty: str = "Intermediate",
    scenario_id: str = "hr_01",
    persona_id: str = "persona_01",
    total_turns: int = 1,
    user_message_count: int = 1,
    assistant_message_count: int = 1,
    total_user_words: int = 20,
    total_user_sentences: int = 2,
    avg_words_per_response: float = 20.0,
    **kwargs,
) -> ConversationAnalysis:
    """Helper to instantiate ConversationAnalysis with all required positional arguments."""
    return ConversationAnalysis(
        session_id=session_id,
        mode=mode,
        difficulty=difficulty,
        scenario_id=scenario_id,
        persona_id=persona_id,
        total_turns=total_turns,
        user_message_count=user_message_count,
        assistant_message_count=assistant_message_count,
        total_user_words=total_user_words,
        total_user_sentences=total_user_sentences,
        avg_words_per_response=avg_words_per_response,
        **kwargs,
    )


# ==============================================================================
# Phase 5: Evaluation Models Validation Tests
# ==============================================================================

def test_score_dimension_valid_bounds():
    """Verify ScoreDimension accepts valid scores between 0 and max_score."""
    dim = ScoreDimension(
        name="Question Handling",
        score=85.5,
        max_score=100.0,
        weight=1.5,
        status=DimensionStatus.EVALUATED.value,
        evidence=["Answered turn 1 question directly."],
        rationale="Clear response.",
    )
    assert dim.score == 85.5
    assert dim.is_evaluated() is True
    assert dim.to_dict()["score"] == 85.5
    assert dim.to_dict()["weight"] == 1.5


def test_score_dimension_invalid_bounds():
    """Verify ScoreDimension raises ValueError for out-of-bounds scores or negative weights."""
    with pytest.raises(ValueError):
        ScoreDimension(name="Invalid", score=-5.0)

    with pytest.raises(ValueError):
        ScoreDimension(name="Invalid", score=105.0, max_score=100.0)

    with pytest.raises(ValueError):
        ScoreDimension(name="Invalid", score=50.0, max_score=0.0)

    with pytest.raises(ValueError):
        ScoreDimension(name="Invalid", score=50.0, weight=-1.0)


def test_score_dimension_status_insufficient_evidence():
    """Verify ScoreDimension correctly reflects insufficient evidence status."""
    dim = ScoreDimension(
        name="Objection Handling",
        score=0.0,
        status=DimensionStatus.INSUFFICIENT_EVIDENCE.value,
        evidence=["No objections posed."],
        rationale="Insufficient evidence.",
    )
    assert dim.is_evaluated() is False
    assert dim.to_dict()["score"] is None
    assert dim.to_dict()["status"] == "insufficient_evidence"


def test_evaluation_result_bounds_and_dict():
    """Verify EvaluationResult validates overall score bounds and serializes to dict."""
    res = EvaluationResult(
        session_id="sess_123",
        mode="HR Interview",
        difficulty="Intermediate",
        overall_score=82.4,
        max_score=100.0,
        strengths=["Great STAR response"],
        improvement_areas=["Add more metrics"],
    )
    assert res.overall_score == 82.4
    d = res.to_dict()
    assert d["session_id"] == "sess_123"
    assert d["overall_score"] == 82.4

    with pytest.raises(ValueError):
        EvaluationResult(
            session_id="sess_123",
            mode="HR Interview",
            difficulty="Intermediate",
            overall_score=120.0,
        )


# ==============================================================================
# Phase 5: Scoring Rules Deterministic Formulas Tests
# ==============================================================================

def test_calculate_question_handling_score_various_ratios():
    """Verify question handling score computes accurate ratios for addressed/partially/unaddressed."""
    analysis = _make_analysis(
        questions_detected=[
            QuestionEvidence(turn_number=1, question_text="What did you do?", status="addressed"),
            QuestionEvidence(turn_number=2, question_text="How did you resolve it?", status="partially_addressed"),
            QuestionEvidence(turn_number=3, question_text="What was the outcome?", status="unaddressed"),
        ],
    )
    dim = calculate_question_handling_score(analysis, weight=1.2)
    assert dim.is_evaluated() is True
    # (1.0 + 0.5 + 0.0) / 3 * 100 = 50.0
    assert dim.score == pytest.approx(50.0, 0.1)
    assert dim.weight == 1.2
    assert len(dim.evidence) == 3


def test_calculate_question_handling_score_no_questions():
    """Verify question handling returns insufficient evidence when no questions exist."""
    analysis = _make_analysis(questions_detected=[])
    dim = calculate_question_handling_score(analysis)
    assert dim.status == DimensionStatus.INSUFFICIENT_EVIDENCE.value
    assert dim.is_evaluated() is False


def test_calculate_topic_coverage_score():
    """Verify topic coverage calculates percentage of covered expected topics."""
    analysis = _make_analysis(
        covered_expected_topics=["Leadership", "Conflict resolution"],
        missing_expected_topics=["Technical depth", "Cost savings"],
    )
    dim = calculate_topic_coverage_score(analysis)
    assert dim.is_evaluated() is True
    # 2 covered out of 4 = 50.0
    assert dim.score == 50.0

    # No expected topics configured
    analysis_empty = _make_analysis()
    dim_empty = calculate_topic_coverage_score(analysis_empty)
    assert dim_empty.status == DimensionStatus.NOT_APPLICABLE.value


def test_calculate_communication_score_penalties():
    """Verify communication score applies deterministic filler, repetition, and brevity penalties."""
    # Clean delivery, medium length
    analysis_clean = _make_analysis(
        user_message_count=2,
        total_user_words=60,
        avg_words_per_response=30.0,
        total_filler_count=0,
        filler_percentage=0.0,
    )
    dim_clean = calculate_communication_score(analysis_clean)
    assert dim_clean.score == 100.0

    # With 4% fillers and 1 repeated phrase
    analysis_penalized = _make_analysis(
        user_message_count=2,
        total_user_words=50,
        avg_words_per_response=25.0,
        total_filler_count=2,
        filler_percentage=4.0,  # 4.0 * 5.0 = 20.0 penalty
        repeated_phrases=[{"phrase": "you know", "count": 2}],  # 1 phrase * 5.0 = 5.0 penalty
    )
    dim_penalized = calculate_communication_score(analysis_penalized)
    # 100 - 20 - 5 = 75.0
    assert dim_penalized.score == 75.0

    # Very short responses (< 10 words)
    analysis_short = _make_analysis(
        user_message_count=2,
        total_user_words=10,
        avg_words_per_response=5.0,
    )
    dim_short = calculate_communication_score(analysis_short)
    # 100 - 15 = 85.0
    assert dim_short.score == 85.0


def test_calculate_relevance_score_and_contradictions():
    """Verify relevance score penalizes contradictions and rewards substantive responses."""
    analysis = _make_analysis(
        user_message_count=2,
        response_features=[
            ResponseFeature(turn_number=1, text="T1", word_count=40, sentence_count=3, avg_sentence_length=13.3, length_category="medium"),
            ResponseFeature(turn_number=2, text="T2", word_count=50, sentence_count=3, avg_sentence_length=16.6, length_category="long"),
        ],
        potential_contradictions=[
            "Turn 1 stated 'I have no cloud experience' vs Turn 2 stated 'I deployed on AWS'."
        ],
    )
    dim = calculate_relevance_score(analysis)
    # base: 70 + (1.0 * 30) = 100. contra penalty: 20. Result: 80.0
    assert dim.score == 80.0
    assert "Contradictions detected: 1" in dim.evidence


def test_calculate_objection_handling_score():
    """Verify objection handling evaluates addressed persona objections."""
    analysis = _make_analysis(
        mode="Client Pitch",
        objections_evidence=[
            ObjectionEvidence(turn_raised=1, objection_type="Budget", objection_text="Too costly", addressed=True),
            ObjectionEvidence(turn_raised=2, objection_type="Security", objection_text="Not SOC2", addressed=False),
        ],
    )
    dim = calculate_objection_handling_score(analysis)
    assert dim.is_evaluated() is True
    assert dim.score == 50.0

    # No objections raised
    analysis_none = _make_analysis(mode="Client Pitch")
    dim_none = calculate_objection_handling_score(analysis_none)
    assert dim_none.status == DimensionStatus.NOT_APPLICABLE.value


# ==============================================================================
# Phase 5: Mode-Specific Evaluators Tests (All 6 Modes)
# ==============================================================================

def test_hr_interview_evaluator():
    """Verify HRInterviewEvaluator produces STAR and specificity scores."""
    from src.intelligence.analysis_models import ModeSpecificEvidence
    analysis = _make_analysis(
        session_id="hr_test",
        mode="HR Interview",
        user_message_count=2,
        total_user_words=80,
        avg_words_per_response=40.0,
        questions_detected=[
            QuestionEvidence(turn_number=1, question_text="Tell me about a challenge", status="addressed")
        ],
        covered_expected_topics=["Conflict resolution"],
        mode_specific_analysis=ModeSpecificEvidence(
            mode="HR Interview",
            indicators={
                "star_components": {
                    "Situation": "detected",
                    "Task": "detected",
                    "Action": "detected",
                    "Result": "detected",
                },
                "specific_metrics_provided": "detected",
            },
        ),
    )
    evaluator = HRInterviewEvaluator()
    result = evaluator.evaluate(analysis)
    assert result.mode == "HR Interview"
    assert len(result.dimensions) == 5

    star_dim = next(d for d in result.dimensions if d.name == "STAR Framework Completeness")
    assert star_dim.score == 100.0
    assert star_dim.weight == 1.5

    spec_dim = next(d for d in result.dimensions if d.name == "Example Specificity & Outcomes")
    assert spec_dim.score == 90.0


def test_technical_interview_evaluator():
    """Verify TechnicalInterviewEvaluator evaluates complexity, edge cases, and technical concepts."""
    from src.intelligence.analysis_models import ModeSpecificEvidence
    analysis = _make_analysis(
        session_id="tech_test",
        mode="Technical Interview",
        difficulty="Hard",
        user_message_count=2,
        total_user_words=100,
        avg_words_per_response=50.0,
        questions_detected=[
            QuestionEvidence(turn_number=1, question_text="What is the runtime?", status="addressed")
        ],
        mode_specific_analysis=ModeSpecificEvidence(
            mode="Technical Interview",
            indicators={
                "technical_concepts": {
                    "Time Complexity": "detected",
                    "Space / Memory Overhead": "detected",
                    "Edge Cases & Boundary Conditions": "detected",
                    "Data Structures & Collections": "detected",
                }
            },
        ),
    )
    evaluator = TechnicalInterviewEvaluator()
    result = evaluator.evaluate(analysis)
    assert result.mode == "Technical Interview"

    comp_dim = next(d for d in result.dimensions if d.name == "Complexity Analysis Rigor")
    assert comp_dim.score == 100.0

    edge_dim = next(d for d in result.dimensions if d.name == "Edge Case & Boundary Reasoning")
    assert edge_dim.score == 90.0


def test_client_pitch_evaluator():
    """Verify ClientPitchEvaluator evaluates value prop, security/compliance, and objections."""
    from src.intelligence.analysis_models import ModeSpecificEvidence
    analysis = _make_analysis(
        session_id="pitch_test",
        mode="Client Pitch",
        difficulty="Hard",
        user_message_count=2,
        total_user_words=120,
        avg_words_per_response=60.0,
        questions_detected=[
            QuestionEvidence(turn_number=1, question_text="What is your ROI?", status="addressed")
        ],
        objections_evidence=[
            ObjectionEvidence(turn_raised=1, objection_type="Price", objection_text="Too high", addressed=True)
        ],
        mode_specific_analysis=ModeSpecificEvidence(
            mode="Client Pitch",
            indicators={
                "pitch_components": {
                    "Value Proposition": "detected",
                    "Cost & ROI Justification": "detected",
                    "Security & Compliance": "detected",
                    "Scalability & Performance": "detected",
                }
            },
        ),
    )
    evaluator = ClientPitchEvaluator()
    result = evaluator.evaluate(analysis)
    assert result.mode == "Client Pitch"

    vp_dim = next(d for d in result.dimensions if d.name == "Value Proposition & Business Impact")
    assert vp_dim.score == 95.0

    sec_dim = next(d for d in result.dimensions if d.name == "Enterprise Security & Scalability")
    assert sec_dim.score == 95.0

    obj_dim = next(d for d in result.dimensions if d.name == "Objection Handling")
    assert obj_dim.score == 100.0


def test_project_viva_evaluator():
    """Verify ProjectVivaEvaluator evaluates architecture, methodology, and limitations."""
    from src.intelligence.analysis_models import ModeSpecificEvidence
    analysis = _make_analysis(
        session_id="viva_test",
        mode="Project Viva",
        difficulty="Intermediate",
        user_message_count=2,
        total_user_words=90,
        avg_words_per_response=45.0,
        questions_detected=[
            QuestionEvidence(turn_number=1, question_text="Why this architecture?", status="addressed")
        ],
        mode_specific_analysis=ModeSpecificEvidence(
            mode="Project Viva",
            indicators={
                "viva_components": {
                    "Architecture & Design Justification": "detected",
                    "Technology Stack Rationale": "detected",
                    "Methodology & Experimental Rigor": "detected",
                    "Awareness of Limitations": "detected",
                }
            },
        ),
    )
    evaluator = ProjectVivaEvaluator()
    result = evaluator.evaluate(analysis)
    assert result.mode == "Project Viva"

    arch_dim = next(d for d in result.dimensions if d.name == "Architecture & Stack Justification")
    assert arch_dim.score == 95.0

    lim_dim = next(d for d in result.dimensions if d.name == "Awareness of Limitations")
    assert lim_dim.score == 90.0


def test_group_discussion_evaluator():
    """Verify GroupDiscussionEvaluator evaluates arguments and collaborative synthesis."""
    from src.intelligence.analysis_models import ModeSpecificEvidence
    analysis = _make_analysis(
        session_id="gd_test",
        mode="Group Discussion",
        difficulty="Intermediate",
        user_message_count=2,
        total_user_words=80,
        avg_words_per_response=40.0,
        mode_specific_analysis=ModeSpecificEvidence(
            mode="Group Discussion",
            indicators={
                "discussion_dynamics": {
                    "Evidence-Backed Reasoning": "detected",
                    "Respectful Counter-Argument / Nuance": "detected",
                    "Constructive Agreement / Building On Ideas": "detected",
                    "Synthesis / Common Ground": "detected",
                }
            },
        ),
    )
    evaluator = GroupDiscussionEvaluator()
    result = evaluator.evaluate(analysis)
    assert result.mode == "Group Discussion"

    collab_dim = next(d for d in result.dimensions if d.name == "Synthesis & Collaborative Dynamics")
    assert collab_dim.score == 95.0


def test_managerial_interview_evaluator():
    """Verify ManagerialInterviewEvaluator evaluates coaching, conflict mediation, and prioritization."""
    from src.intelligence.analysis_models import ModeSpecificEvidence
    analysis = _make_analysis(
        session_id="mgr_test",
        mode="Managerial Interview",
        difficulty="Hard",
        user_message_count=2,
        total_user_words=100,
        avg_words_per_response=50.0,
        mode_specific_analysis=ModeSpecificEvidence(
            mode="Managerial Interview",
            indicators={
                "leadership_signals": {
                    "Empathetic Leadership & 1-on-1 Communication": "detected",
                    "Conflict Mediation & De-escalation": "detected",
                    "Prioritization Frameworks": "detected",
                    "Ownership & Accountability": "detected",
                }
            },
        ),
    )
    evaluator = ManagerialInterviewEvaluator()
    result = evaluator.evaluate(analysis)
    assert result.mode == "Managerial Interview"

    emp_dim = next(d for d in result.dimensions if d.name == "Leadership Empathy & Coaching")
    assert emp_dim.score == 90.0

    conf_dim = next(d for d in result.dimensions if d.name == "Conflict Mediation & De-escalation")
    assert conf_dim.score == 90.0


# ==============================================================================
# Phase 5: Central EvaluationEngine End-to-End Tests
# ==============================================================================

def test_evaluation_engine_full_workflow():
    """
    Verify full end-to-end evaluation flow:
    Session -> Analysis -> Evaluation Engine -> Normalized Overall Score & Explainability.
    """
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("hr_behavioral_02")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona)

    # Turn 1
    conv_mgr.send_user_message(
        session,
        "In my previous project, two engineers had a conflict over API architecture. "
        "As tech lead, I organized a 1-on-1 session to understand each viewpoint.",
        scenario,
        persona,
    )
    # Turn 2
    conv_mgr.send_user_message(
        session,
        "I defined a structured evaluation framework. We aligned on GraphQL, reducing API latency by 35% "
        "and meeting our Q3 deadline without missing milestone targets.",
        scenario,
        persona,
    )

    conv_mgr.end_session(session)

    # Phase 4 analysis
    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session, scenario, persona)

    # Phase 5 evaluation
    engine = EvaluationEngine()
    evaluation = engine.evaluate(analysis, scenario, persona)

    # Assertions
    assert evaluation.session_id == session.session_id
    assert evaluation.mode == "HR Interview"
    assert 0.0 <= evaluation.overall_score <= 100.0
    assert evaluation.overall_score > 0.0
    assert len(evaluation.dimensions) >= 4
    assert len(evaluation.strengths) > 0
    assert len(evaluation.improvement_areas) > 0


    # Ensure all dimensions are properly formatted
    for dim in evaluation.dimensions:
        assert dim.max_score == 100.0
        if dim.is_evaluated():
            assert 0.0 <= dim.score <= 100.0
        assert len(dim.rationale) > 0


def test_evaluation_engine_empty_session_safe_handling():
    """Verify EvaluationEngine handles an empty session safely with 0.0 overall score and no exceptions."""
    session = PracticeSession(
        scenario_id="hr_intro_01",
        persona_id="persona_hr_friendly",
        mode="HR Interview",
        status=SessionStatus.ACTIVE.value,
    )
    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session)

    engine = EvaluationEngine()
    evaluation = engine.evaluate(analysis)

    assert evaluation.overall_score == 0.0
    assert len(evaluation.insufficient_evidence_dimensions) > 0
    assert "STAR Framework Completeness" in evaluation.insufficient_evidence_dimensions


def test_evaluation_engine_determinism_and_consistency():
    """Verify evaluating the exact same analysis produces identical scores every time."""
    scenario_mgr = ScenarioManager()
    scenario = scenario_mgr.get_scenario_by_id("tech_python_01")
    persona = scenario_mgr.get_persona_by_id(scenario.persona_id)

    conv_mgr = ConversationManager()
    session = conv_mgr.start_session(scenario, persona)
    conv_mgr.send_user_message(
        session,
        "We can use a hash map lookup with O(1) time complexity and minimal space memory overhead. "
        "For edge cases, empty input lists and single element arrays are validated at the beginning.",
        scenario,
        persona,
    )
    conv_mgr.end_session(session)

    analyzer = ConversationAnalyzer()
    analysis = analyzer.analyze(session, scenario, persona)

    engine = EvaluationEngine()
    eval1 = engine.evaluate(analysis, scenario, persona)
    eval2 = engine.evaluate(analysis, scenario, persona)

    assert eval1.overall_score == eval2.overall_score
    assert len(eval1.dimensions) == len(eval2.dimensions)
    for d1, d2 in zip(eval1.dimensions, eval2.dimensions):
        assert d1.name == d2.name
        assert d1.score == d2.score
        assert d1.rationale == d2.rationale


