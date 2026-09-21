"""
Pitch Practice Partner — AI Interview & Communication Simulator
Phase 6: Explainable Feedback Engine
"""

import streamlit as st
from typing import Optional

from src.scenarios.scenario_manager import ScenarioManager
from src.scenarios.scenario_models import (
    Scenario,
    Persona,
    PRACTICE_MODES,
    DIFFICULTY_LEVELS,
)
from src.conversation.conversation_manager import ConversationManager
from src.conversation.conversation_models import PracticeSession, SessionStatus
from src.intelligence.conversation_analyzer import ConversationAnalyzer
from src.intelligence.analysis_models import ConversationAnalysis
from src.evaluation.evaluation_engine import EvaluationEngine
from src.evaluation.evaluation_models import EvaluationResult, DimensionStatus
from src.feedback import (
    FeedbackEngine,
    FeedbackResult,
    FeedbackPriority,
    EvidenceType,
    format_evidence_display,
)
from src.history import (
    HistoryService,
    AnalyticsService,
    HistoricalSession,
    compare_sessions,
    DEFAULT_DB_PATH,
)
from src.ai.provider import get_ai_provider
from src.utils import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    APP_TAGLINE,
    MODE_ICONS,
    DIFFICULTY_BADGES,
)


CUSTOM_CSS = """
<style>
    /* Global Card & Container Styles */
    .metric-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #3b82f6;
    }
    .score-hero-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(16, 185, 129, 0.12) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        text-align: center;
    }
    .persona-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(147, 51, 234, 0.05) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }
    .evidence-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .dimension-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .mode-badge {
        display: inline-block;
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .diff-badge {
        display: inline-block;
        background-color: #f3f4f6;
        color: #1f2937;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .banner-demo {
        background-color: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 20px;
    }
    .banner-active {
        background-color: rgba(59, 130, 246, 0.08);
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 16px;
    }
    .banner-completed {
        background-color: rgba(16, 185, 129, 0.08);
        border-left: 4px solid #10b981;
        padding: 14px 18px;
        border-radius: 0 8px 8px 0;
        margin-bottom: 16px;
    }
    .tag-chip {
        display: inline-block;
        background-color: rgba(59, 130, 246, 0.1);
        color: #1d4ed8;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .tag-missing {
        display: inline-block;
        background-color: rgba(239, 68, 68, 0.1);
        color: #b91c1c;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .strength-item {
        background-color: rgba(16, 185, 129, 0.08);
        border-left: 3px solid #10b981;
        padding: 8px 12px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 8px;
    }
    .improve-item {
        background-color: rgba(245, 158, 11, 0.08);
        border-left: 3px solid #f59e0b;
        padding: 8px 12px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 8px;
    }
    .feedback-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .action-callout {
        background-color: rgba(59, 130, 246, 0.08);
        border-left: 4px solid #3b82f6;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        margin-top: 8px;
        font-size: 0.92rem;
    }
    .badge-priority-high {
        display: inline-block;
        background-color: rgba(239, 68, 68, 0.15);
        color: #b91c1c;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-priority-med {
        display: inline-block;
        background-color: rgba(245, 158, 11, 0.15);
        color: #b45309;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-priority-low {
        display: inline-block;
        background-color: rgba(16, 185, 129, 0.15);
        color: #047857;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
"""


def init_session_state() -> None:
    """Initialize application session state variables."""
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "Home"
    if "selected_mode" not in st.session_state:
        st.session_state.selected_mode = PRACTICE_MODES[0]
    if "selected_difficulty" not in st.session_state:
        st.session_state.selected_difficulty = DIFFICULTY_LEVELS[0]
    if "selected_scenario_id" not in st.session_state:
        st.session_state.selected_scenario_id = None
    if "is_practicing" not in st.session_state:
        st.session_state.is_practicing = False
    if "active_session" not in st.session_state:
        st.session_state.active_session = None
    if "current_analysis" not in st.session_state:
        st.session_state.current_analysis = None
    if "current_evaluation" not in st.session_state:
        st.session_state.current_evaluation = None
    if "current_feedback" not in st.session_state:
        st.session_state.current_feedback = None
    if "scenario_manager" not in st.session_state:
        st.session_state.scenario_manager = ScenarioManager()
    if "ai_provider" not in st.session_state:
        st.session_state.ai_provider = get_ai_provider()
    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = ConversationManager(
            ai_provider=st.session_state.ai_provider
        )
    if "conversation_analyzer" not in st.session_state:
        st.session_state.conversation_analyzer = ConversationAnalyzer()
    if "evaluation_engine" not in st.session_state:
        st.session_state.evaluation_engine = EvaluationEngine()
    if "feedback_engine" not in st.session_state:
        st.session_state.feedback_engine = FeedbackEngine()
    if "history_service" not in st.session_state:
        st.session_state.history_service = HistoryService()
    if "analytics_service" not in st.session_state:
        st.session_state.analytics_service = AnalyticsService(history_service=st.session_state.history_service)
    if "selected_history_session_id" not in st.session_state:
        st.session_state.selected_history_session_id = None
    if "saved_session_id" not in st.session_state:
        st.session_state.saved_session_id = None


def render_sidebar() -> None:
    """Render the sidebar navigation and application status."""
    ai_provider = st.session_state.ai_provider
    status = ai_provider.get_status()

    with st.sidebar:
        st.markdown(f"## 🎙️ {APP_NAME}")
        st.caption(f"**{APP_SUBTITLE}**")

        # Provider Status Tag
        badge_class = "banner-demo" if status.is_demo else "banner-active"
        st.markdown(
            f"""
            <div class="{badge_class}">
                <strong>⚡ {status.name.upper()}</strong><br>
                <small style="color: #666;">Model: {status.model_name}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### 🧭 Navigation")

        pages = ["Home", "Practice", "History", "Analytics", "Settings"]
        selected = st.radio(
            "Select Page",
            pages,
            index=pages.index(st.session_state.nav_page),
            label_visibility="collapsed",
        )

        if selected != st.session_state.nav_page:
            st.session_state.nav_page = selected
            st.rerun()

        st.markdown("---")
        st.caption(f"**Version:** {APP_VERSION}")
        st.caption(f"**Phase:** Phase 7 — Session History & Analytics")


def render_home_page(scenario_mgr: ScenarioManager) -> None:
    """Render the landing and dashboard page."""
    st.markdown(f"# 🎙️ {APP_NAME}")
    st.markdown(f"### *{APP_SUBTITLE}*")
    st.markdown(f"#### **{APP_TAGLINE}**")

    status = st.session_state.ai_provider.get_status()
    st.markdown(
        f"""
        <div class="banner-demo">
            <strong>ℹ️ Active Engine:</strong> Operating in <strong>{status.name}</strong> mode with 
            integrated <strong>Explainable Feedback Engine</strong> and <strong>Session History & Analytics (Phase 7)</strong>. 
            Complete realistic simulations, receive transparent WHAT / WHY / EVIDENCE / IMPACT / ACTION guidance, 
            and track your longitudinal progress over time.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        Traditional practice tools rely on static question lists and one-way monologues. 
        **Pitch Practice Partner** provides interactive, dynamic communication simulations—allowing 
        you to practice realistic interviews, executive pitches, academic defenses, and team debates with 
        specialized, personality-driven conversational AI personas.
        """
    )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🚀 Start Practice Now", type="primary", use_container_width=True):
            st.session_state.nav_page = "Practice"
            st.rerun()
    with col2:
        if st.button("⚙️ View Settings", use_container_width=True):
            st.session_state.nav_page = "Settings"
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Supported Practice Modes")
    st.markdown("Explore the specialized communication environments and persona archetypes:")

    cols = st.columns(3)
    modes_info = [
        ("HR Interview", "👔", "Behavioral & cultural fit questions, STAR method responses, and background introductions."),
        ("Technical Interview", "💻", "Algorithmic thinking, system architecture defense, and trade-off explanations."),
        ("Client Pitch", "🚀", "Executive value propositions, enterprise product demos, and investor pitches."),
        ("Project Viva", "🎓", "Academic project defenses, design choice justifications, and methodology critiques."),
        ("Group Discussion", "👥", "Collaborative debates, viewpoint structuring, and active listening skills."),
        ("Managerial Interview", "🧭", "Team leadership, conflict mediation, priority alignment, and crisis management."),
    ]

    for idx, (mode_name, icon, desc) in enumerate(modes_info):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"#### {icon} {mode_name}")
                st.write(desc)
                scenarios_count = len(scenario_mgr.get_scenarios_by_mode(mode_name))
                personas_count = len(scenario_mgr.get_personas_by_mode(mode_name))
                st.caption(f"📚 {scenarios_count} scenario(s) • 🎭 {personas_count} persona(s)")
                if st.button(f"Practice {mode_name}", key=f"btn_mode_{idx}", use_container_width=True):
                    st.session_state.selected_mode = mode_name
                    st.session_state.is_practicing = False
                    st.session_state.active_session = None
                    st.session_state.current_analysis = None
                    st.session_state.current_evaluation = None
                    st.session_state.nav_page = "Practice"
                    st.rerun()


def render_practice_page(scenario_mgr: ScenarioManager) -> None:
    """Render the interactive role-play practice chat simulator, analysis, and evaluation view."""
    conv_mgr: ConversationManager = st.session_state.conversation_manager
    analyzer: ConversationAnalyzer = st.session_state.conversation_analyzer
    eval_engine: EvaluationEngine = st.session_state.evaluation_engine

    # --------------------------------------------------------------------------
    # 1. Setup Interface (when session is not active)
    # --------------------------------------------------------------------------
    if not st.session_state.is_practicing:
        st.markdown("## 🎯 Practice Setup & Persona Selection")
        st.markdown("Select a communication mode, difficulty level, and scenario below:")

        col_mode, col_diff = st.columns(2)
        with col_mode:
            selected_mode = st.selectbox(
                "Select Practice Mode",
                PRACTICE_MODES,
                index=PRACTICE_MODES.index(st.session_state.selected_mode)
                if st.session_state.selected_mode in PRACTICE_MODES
                else 0,
            )
            st.session_state.selected_mode = selected_mode

        with col_diff:
            selected_difficulty = st.selectbox(
                "Select Difficulty",
                DIFFICULTY_LEVELS,
                index=DIFFICULTY_LEVELS.index(st.session_state.selected_difficulty)
                if st.session_state.selected_difficulty in DIFFICULTY_LEVELS
                else 0,
            )
            st.session_state.selected_difficulty = selected_difficulty

        available_scenarios = scenario_mgr.get_scenarios_by_mode(selected_mode)

        st.markdown("---")
        st.markdown("### 📋 Available Scenarios")

        if not available_scenarios:
            st.info("No scenarios found for the selected mode.")
            return

        scenario_options = {f"{s.name} ({s.difficulty})": s.id for s in available_scenarios}
        scenario_labels = list(scenario_options.keys())

        current_selected_id = st.session_state.selected_scenario_id
        default_idx = 0
        if current_selected_id:
            for idx, (label, sid) in enumerate(scenario_options.items()):
                if sid == current_selected_id:
                    default_idx = idx
                    break

        chosen_label = st.selectbox(
            "Choose a Scenario to Practice",
            scenario_labels,
            index=default_idx,
        )
        chosen_scenario_id = scenario_options[chosen_label]
        st.session_state.selected_scenario_id = chosen_scenario_id

        scenario: Optional[Scenario] = scenario_mgr.get_scenario_by_id(chosen_scenario_id)
        persona: Optional[Persona] = scenario_mgr.get_persona_for_scenario(chosen_scenario_id)

        if scenario and persona:
            # Scenario Overview Card
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>{MODE_ICONS.get(scenario.mode, '🎯')} {scenario.name}</h3>
                    <span class="mode-badge">{scenario.mode}</span>
                    <span class="diff-badge">{DIFFICULTY_BADGES.get(scenario.difficulty, scenario.difficulty)}</span>
                    <p style="margin-top: 12px; font-size: 1.05rem;">{scenario.description}</p>
                    <p><strong>🎯 Candidate Goal:</strong> {scenario.conversation_goal or scenario.objective}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Persona Card
            st.markdown(
                f"""
                <div class="persona-card">
                    <h4>🤖 Simulated AI Persona: {persona.name} <small style="color: #6366f1;">({persona.role})</small></h4>
                    <p><em>"{persona.background}"</em></p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px;">
                        <div>
                            <strong>🧠 Personality:</strong> {persona.personality}<br>
                            <strong>🗣️ Style:</strong> {persona.communication_style}<br>
                            <strong>⚡ Persona Difficulty:</strong> {persona.difficulty}
                        </div>
                        <div>
                            <strong>🎯 Persona Objective:</strong> {persona.objective}<br>
                            <strong>📚 Knowledge Level:</strong> {persona.knowledge_level}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                with st.expander("🔍 Persona Core Concerns & Probing Focus", expanded=True):
                    for concern in persona.concerns:
                        st.markdown(f"- ⚠️ **{concern}**")
            with col_p2:
                with st.expander("💬 Observable Behaviors & Objection Tendencies", expanded=True):
                    for beh in persona.behaviors:
                        st.markdown(f"- {beh}")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Start Interactive Practice Session", type="primary", use_container_width=True):
                # Start new conversation session
                st.session_state.active_session = conv_mgr.start_session(
                    scenario=scenario,
                    persona=persona,
                    difficulty=st.session_state.selected_difficulty,
                )
                st.session_state.current_analysis = None
                st.session_state.current_evaluation = None
                st.session_state.current_feedback = None
                st.session_state.is_practicing = True
                st.rerun()

    # --------------------------------------------------------------------------
    # 2. Interactive Role-Play Chat Session
    # --------------------------------------------------------------------------
    else:
        session: PracticeSession = st.session_state.active_session
        scenario = scenario_mgr.get_scenario_by_id(session.scenario_id)
        persona = scenario_mgr.get_persona_by_id(session.persona_id)

        if not scenario or not persona:
            st.error("Session configuration error: Scenario or Persona data not found.")
            if st.button("Return to Setup"):
                st.session_state.is_practicing = False
                st.session_state.active_session = None
                st.session_state.current_analysis = None
                st.session_state.current_evaluation = None
                st.session_state.current_feedback = None
                st.rerun()
            return

        # Session Header Banner
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.markdown(f"## 🎙️ {scenario.name}")
            st.markdown(
                f"**Role-Play Simulation** with **{persona.name}** ({persona.role}) • "
                f"`{session.mode}` • `{session.difficulty}`"
            )
        with header_col2:
            st.metric(
                label="Turn Progress",
                value=f"{session.turn_number} / {session.max_turns}",
                delta=f"{session.max_turns - session.turn_number} turns remaining"
                if session.turn_number < session.max_turns
                else "Finished",
            )

        # Control Action Buttons
        ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1, 1, 2])
        with ctrl_c1:
            if st.button("🔄 Restart Session", use_container_width=True):
                st.session_state.active_session = conv_mgr.restart_session(
                    scenario=scenario,
                    persona=persona,
                    difficulty=session.difficulty,
                )
                st.session_state.current_analysis = None
                st.session_state.current_evaluation = None
                st.session_state.current_feedback = None
                st.session_state.saved_session_id = None
                st.rerun()
        with ctrl_c2:
            if session.is_active():
                if st.button("⏹️ End Session", use_container_width=True):
                    st.session_state.active_session = conv_mgr.end_session(session)
                    st.rerun()
        with ctrl_c3:
            if st.button("⚙️ Change Scenario / Setup", use_container_width=True):
                st.session_state.is_practicing = False
                st.session_state.active_session = None
                st.session_state.current_analysis = None
                st.session_state.current_evaluation = None
                st.session_state.current_feedback = None
                st.session_state.saved_session_id = None
                st.rerun()

        st.markdown("---")

        # Render Chat History
        for msg in session.conversation_history:
            if msg.role == "assistant":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(f"**{persona.name}** *({persona.role})*")
                    st.markdown(msg.content)
            elif msg.role == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown("**You**")
                    st.markdown(msg.content)

        # Active Chat Input (when session is active)
        if session.is_active():
            user_input = st.chat_input(
                placeholder=f"Respond to {persona.name} as you would in a real {scenario.mode}..."
            )

            if user_input:
                try:
                    with st.spinner(f"{persona.name} is thinking..."):
                        updated_session, _ = conv_mgr.send_user_message(
                            session=session,
                            user_content=user_input,
                            scenario=scenario,
                            persona=persona,
                        )
                        st.session_state.active_session = updated_session
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing response: {e}")

        # Render Session Completion, Analysis & Evaluation
        elif session.is_completed():
            st.markdown(
                """
                <div class="banner-completed">
                    <h4>🏁 Practice Session Completed</h4>
                    <p>You have reached the conclusion of this practice simulation scenario.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Action Buttons: Analyze vs Evaluate
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("📊 View Conversation Evidence (Phase 4)", use_container_width=True):
                    if st.session_state.current_analysis is None:
                        with st.spinner("Extracting conversation intelligence..."):
                            st.session_state.current_analysis = analyzer.analyze(session, scenario, persona)
                    st.rerun()

            with col_act2:
                if st.button("🏆 Evaluate Performance & Generate Explainable Feedback (Phase 6)", type="primary", use_container_width=True):
                    if st.session_state.current_analysis is None:
                        with st.spinner("Extracting conversation evidence first..."):
                            st.session_state.current_analysis = analyzer.analyze(session, scenario, persona)
                    with st.spinner("Calculating explainable dimensional scores..."):
                        st.session_state.current_evaluation = eval_engine.evaluate(
                            analysis=st.session_state.current_analysis,
                            scenario=scenario,
                            persona=persona,
                        )
                    with st.spinner("Synthesizing explainable feedback (WHAT / WHY / EVIDENCE / IMPACT / ACTION)..."):
                        st.session_state.current_feedback = st.session_state.feedback_engine.generate_feedback(
                            analysis=st.session_state.current_analysis,
                            evaluation=st.session_state.current_evaluation,
                            session=session,
                            scenario=scenario,
                            persona=persona,
                        )
                    st.rerun()

            # Render Evaluation & Feedback Result (Phase 5 & 6)
            if st.session_state.current_evaluation is not None:
                if st.session_state.current_feedback is None and st.session_state.current_analysis is not None:
                    st.session_state.current_feedback = st.session_state.feedback_engine.generate_feedback(
                        analysis=st.session_state.current_analysis,
                        evaluation=st.session_state.current_evaluation,
                        session=session,
                        scenario=scenario,
                        persona=persona,
                    )

                # Persist completed session to persistent SQLite history (idempotent, once per session)
                if st.session_state.get("saved_session_id") != session.session_id:
                    try:
                        st.session_state.history_service.save_completed_session(
                            session=session,
                            scenario=scenario,
                            persona=persona,
                            evaluation=st.session_state.current_evaluation,
                            feedback=st.session_state.current_feedback,
                        )
                        st.session_state.saved_session_id = session.session_id
                    except Exception as err:
                        st.warning(f"Could not persist session to local history: {err}")

                render_evaluation_report(st.session_state.current_evaluation, st.session_state.current_feedback)

            # Render Conversation Analysis (Phase 4)
            if st.session_state.current_analysis is not None and st.session_state.current_evaluation is None:
                render_conversation_analysis_report(st.session_state.current_analysis)


def render_evaluation_report(
    evaluation: EvaluationResult,
    feedback: Optional[FeedbackResult] = None
) -> None:
    """
    Render structured, explainable performance evaluation with overall scores,
    dimensional breakdowns, and evidence-backed WHAT / WHY / EVIDENCE / IMPACT / ACTION feedback.
    """
    st.markdown("---")
    st.markdown("## 🏆 Performance Evaluation & Explainable Feedback Report (Phase 6)")
    st.caption("Deterministic, evidence-grounded performance assessment with transparent WHAT / WHY / EVIDENCE / IMPACT / ACTION breakdown.")

    # 1. Overall Score Hero Card
    st.markdown(
        f"""
        <div class="score-hero-card">
            <h1 style="font-size: 3rem; margin: 0; color: #1e40af;">{evaluation.overall_score:.1f} <span style="font-size: 1.5rem; color: #64748b;">/ {evaluation.max_score:.0f}</span></h1>
            <p style="font-size: 1.15rem; margin-top: 8px; font-weight: 600; color: #1e293b;">Overall Performance Score</p>
            <span class="mode-badge">{evaluation.mode}</span>
            <span class="diff-badge">{evaluation.difficulty}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, max(0.0, evaluation.overall_score / 100.0)))

    # 2. Executive Feedback Summary (Phase 6)
    if feedback and feedback.overall_summary:
        st.markdown(
            f"""
            <div class="feedback-card" style="border-left: 4px solid #3b82f6;">
                <h4 style="margin: 0 0 6px 0; color: #1e40af;">💡 Executive Feedback Summary</h4>
                <p style="margin: 0; font-size: 0.98rem; line-height: 1.5;">{feedback.overall_summary}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Priority Practice Actions (Phase 6)
    if feedback and feedback.priority_actions:
        st.markdown("### 🎯 Priority Practice Actions for Next Session")
        st.caption("Key practical adjustments to execute during your next practice turn.")
        action_cols = st.columns(min(len(feedback.priority_actions), 3))
        for i, act in enumerate(feedback.priority_actions[:3]):
            badge_cls = (
                "badge-priority-high"
                if act.priority == "High Priority"
                else ("badge-priority-med" if act.priority == "Medium Priority" else "badge-priority-low")
            )
            with action_cols[i % len(action_cols)]:
                st.markdown(
                    f"""
                    <div class="feedback-card" style="height: 100%;">
                        <span class="{badge_cls}">{act.priority}</span>
                        <h4 style="margin: 8px 0 6px 0; font-size: 1.05rem;">{act.title}</h4>
                        <div class="action-callout">
                            <strong>Guideline:</strong> {act.action}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 4. Strengths & Key Improvements (Side-by-side)
    col_str, col_imp = st.columns(2)
    with col_str:
        st.markdown("### 🌟 Evidence-Backed Strengths")
        if feedback and feedback.strengths:
            for s in feedback.strengths:
                s_evi = format_evidence_display(s.evidence, evidence_type=s.evidence_type, source_reference=s.source_reference)
                st.markdown(
                    f"""
                    <div class="strength-item" style="margin-bottom: 12px; padding: 12px 14px;">
                        <h4 style="margin: 0 0 4px 0; color: #065f46;">✓ {s.title}</h4>
                        <p style="margin: 0 0 4px 0; font-size: 0.9rem;"><strong>WHAT:</strong> {s.what}</p>
                        <p style="margin: 0 0 4px 0; font-size: 0.85rem; color: #047857;"><strong>EVIDENCE:</strong> <em>{s_evi}</em></p>
                        <p style="margin: 0; font-size: 0.85rem; color: #475569;"><strong>IMPACT:</strong> {s.impact}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            for s in evaluation.strengths:
                st.markdown(f'<div class="strength-item">✓ {s}</div>', unsafe_allow_html=True)

    with col_imp:
        st.markdown("### 📈 Key Actionable Improvement Areas")
        if feedback and feedback.improvements:
            for imp in feedback.improvements:
                badge_cls = (
                    "badge-priority-high"
                    if imp.priority == "High Priority"
                    else ("badge-priority-med" if imp.priority == "Medium Priority" else "badge-priority-low")
                )
                imp_evi = format_evidence_display(imp.evidence, evidence_type=imp.evidence_type, source_reference=imp.source_reference)
                st.markdown(
                    f"""
                    <div class="improve-item" style="margin-bottom: 12px; padding: 12px 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <h4 style="margin: 0; color: #92400e;">⚡ {imp.title}</h4>
                            <span class="{badge_cls}">{imp.priority}</span>
                        </div>
                        <p style="margin: 0 0 4px 0; font-size: 0.9rem;"><strong>WHAT:</strong> {imp.what}</p>
                        <p style="margin: 0 0 4px 0; font-size: 0.85rem; color: #92400e;"><strong>WHY:</strong> {imp.why}</p>
                        <p style="margin: 0 0 6px 0; font-size: 0.85rem; color: #475569;"><strong>EVIDENCE:</strong> <em>{imp_evi}</em></p>
                        <div class="action-callout" style="margin-top: 4px; padding: 8px 10px;">
                            <strong style="color: #1e40af;">ACTION:</strong> {imp.action}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            for imp in evaluation.improvement_areas:
                st.markdown(f'<div class="improve-item">⚡ {imp}</div>', unsafe_allow_html=True)

    # 5. Detailed Dimension Breakdown & Explainable Feedback
    st.markdown("---")
    st.markdown("### 📊 Dimension Breakdown & Explainable Feedback")
    st.caption("Each score connects Phase 5 scoring → Phase 4 factual evidence → WHAT/WHY explanation → Scenario IMPACT → Practical ACTION.")

    feedback_map = {item.dimension: item for item in feedback.items} if feedback else {}

    for dim in evaluation.dimensions:
        with st.container():
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                if dim.is_evaluated():
                    st.markdown(f"#### **{dim.name}**")
                    st.write(f"**Rationale:** {dim.rationale}")
                else:
                    st.markdown(f"#### **{dim.name}** *(Status: {dim.status.replace('_', ' ').upper()})*")
                    st.write(f"*{dim.rationale}*")

            with col_d2:
                if dim.is_evaluated():
                    st.metric("Score", f"{dim.score:.1f} / {dim.max_score:.0f}")
                else:
                    st.metric("Score", "N/A")

            if dim.is_evaluated():
                st.progress(min(1.0, max(0.0, dim.score / 100.0)))

            item = feedback_map.get(dim.name)
            if item:
                badge_cls = (
                    "badge-priority-high"
                    if item.priority == "High Priority"
                    else ("badge-priority-med" if item.priority == "Medium Priority" else "badge-priority-low")
                )
                with st.expander(f"💡 Explainable Feedback for {dim.name} ({item.priority})", expanded=False):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        st.markdown(f"**🔍 WHAT was observed:**\n\n{item.what}")
                        st.markdown(f"**⚖️ WHY it affected evaluation:**\n\n{item.why}")
                    with col_f2:
                        st.markdown(f"**🌐 Real-World IMPACT ({evaluation.mode}):**\n\n{item.impact}")
                        formatted_evi = format_evidence_display(
                            item.evidence,
                            evidence_type=item.evidence_type,
                            source_reference=item.source_reference,
                        )
                        st.markdown(f"**📜 EVIDENCE:**\n\n_{formatted_evi}_")
                    st.markdown(
                        f"""
                        <div class="action-callout">
                            <strong style="color: #1e40af;">🚀 ACTION FOR NEXT SESSION:</strong> {item.action}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            elif dim.evidence:
                with st.expander(f"🔍 View Evidence Items for {dim.name}", expanded=False):
                    for evi_item in dim.evidence:
                        st.markdown(f"- {evi_item}")
            st.markdown("---")

    if feedback and feedback.insufficient_evidence_notes:
        st.info(
            "ℹ️ **Competencies Requiring Additional Scenario Evidence:**\n\n"
            + "\n".join(f"- {note}" for note in feedback.insufficient_evidence_notes)
        )
    elif evaluation.insufficient_evidence_dimensions:
        st.info(
            f"ℹ️ **Dimensions with Insufficient Evidence:** {', '.join(evaluation.insufficient_evidence_dimensions)}. "
            "These dimensions require additional conversation turns or specific scenario triggers to be reliably scored."
        )

    if evaluation.mode_specific_evaluation and evaluation.mode_specific_evaluation.mode_notes:
        with st.expander("ℹ️ Domain Evaluation Notes & Methodology", expanded=False):
            for note in evaluation.mode_specific_evaluation.mode_notes:
                st.markdown(f"- {note}")


def render_conversation_analysis_report(analysis: ConversationAnalysis) -> None:
    """
    Render structured, evidence-based conversation intelligence report (Phase 4).
    """
    st.markdown("---")
    st.markdown("## 🔍 Conversation Intelligence Evidence Report (Phase 4)")
    st.caption("Factual analysis of dialogue turns, linguistic features, question responses, and topical coverage.")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Turns", f"{analysis.total_turns}")
    with m2:
        st.metric("User Responses", f"{analysis.user_message_count}")
    with m3:
        st.metric("Total User Words", f"{analysis.total_user_words}")
    with m4:
        st.metric("Avg Words / Response", f"{analysis.avg_words_per_response:.1f}")

    tab_resp, tab_qa, tab_topics, tab_signals, tab_mode = st.tabs([
        "📝 Response Features",
        "❓ Questions & Alignment",
        "🎯 Topical Coverage",
        "🗣️ Language Signals",
        "👔 Mode Evidence",
    ])

    with tab_resp:
        st.markdown("### 📝 Turn-by-Turn Linguistic Features (Deterministic)")
        for rf in analysis.response_features:
            with st.container():
                st.markdown(f"**Turn {rf.turn_number}** • Category: `{rf.length_category.upper()}`")
                st.markdown(f"> *\"{rf.text}\"*")
                c1, c2, c3 = st.columns(3)
                c1.write(f"📊 **Words:** {rf.word_count}")
                c2.write(f"📏 **Sentences:** {rf.sentence_count}")
                c3.write(f"📐 **Avg Sentence Length:** {rf.avg_sentence_length:.1f} words")
                st.markdown("---")

    with tab_qa:
        st.markdown("### ❓ AI Questions & Candidate Alignment (Heuristic Observation)")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            st.metric("Questions Addressed", f"{analysis.answered_questions_count}")
        with col_q2:
            st.metric("Potentially Unaddressed", f"{analysis.unanswered_questions_count}")

        for q in analysis.questions_detected:
            status_icon = "✅" if q.status == "addressed" else ("⚠️" if q.status == "partially_addressed" else "❌")
            st.markdown(
                f"""
                <div class="evidence-card">
                    <strong>{status_icon} Turn {q.turn_number}:</strong> <em>\"{q.question_text}\"</em><br>
                    <small><strong>Topic:</strong> {q.detected_topic} | <strong>Alignment:</strong> {q.status.replace('_', ' ').capitalize()}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_topics:
        st.markdown("### 🎯 Topical Coverage & Persona Concerns (Evidence)")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("#### ✅ Covered Expected Topics")
            if analysis.covered_expected_topics:
                for topic in analysis.covered_expected_topics:
                    st.markdown(f'<span class="tag-chip">✓ {topic}</span>', unsafe_allow_html=True)
            else:
                st.write("No configured expected topics detected.")

        with col_t2:
            st.markdown("#### ⏳ Expected Topics Not Detected")
            if analysis.missing_expected_topics:
                for topic in analysis.missing_expected_topics:
                    st.markdown(f'<span class="tag-missing">✗ {topic}</span>', unsafe_allow_html=True)
            else:
                st.write("All expected topics detected in candidate responses.")

        st.markdown("---")
        st.markdown("#### 🤖 Persona Concerns Alignment")
        for c in analysis.concerns_evidence:
            st.write(f"- **{c.concern_name}:** `{c.status.replace('_', ' ').capitalize()}`")

        if analysis.objections_evidence:
            st.markdown("#### 🛡️ Objections Raised & Addressed")
            for obj in analysis.objections_evidence:
                st.write(f"- **{obj.objection_type}:** `{'Addressed with evidence' if obj.addressed else 'Unaddressed'}`")

    with tab_signals:
        st.markdown("### 🗣️ Language & Repetition Signals")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("#### 🎙️ Vocal Hesitations & Filler Words")
            st.write(f"**Total Fillers Detected:** {analysis.total_filler_count} ({analysis.filler_percentage:.1f}% of words)")
            if analysis.filler_word_counts:
                for word, count in analysis.filler_word_counts.items():
                    st.write(f"- `\"{word}\"`: {count} occurrence(s)")
            else:
                st.write("No significant filler words detected.")

        with col_s2:
            st.markdown("#### 🔁 Repeated Phrases & Keywords")
            if analysis.repeated_phrases:
                for p in analysis.repeated_phrases:
                    st.write(f"- Phrase *\"{p['phrase']}\"*: {p['count']} times")
            elif analysis.repeated_words:
                for w in analysis.repeated_words[:4]:
                    st.write(f"- Keyword *\"{w['word']}\"*: {w['count']} times")
            else:
                st.write("No excessive phrase repetition detected.")

        if analysis.potential_contradictions:
            st.markdown("---")
            st.markdown("#### ⚠️ Potential Inconsistencies / Contradictions (Observation)")
            for contra in analysis.potential_contradictions:
                st.warning(contra)

    with tab_mode:
        if analysis.mode_specific_analysis:
            st.markdown(f"### 👔 {analysis.mode} Specific Evidence")
            indicators = analysis.mode_specific_analysis.indicators

            for key, val in indicators.items():
                st.markdown(f"#### **{key.replace('_', ' ').capitalize()}**")
                if isinstance(val, dict):
                    for sub_k, sub_v in val.items():
                        icon = "✅" if sub_v == "detected" else "⚪"
                        st.write(f"{icon} **{sub_k}:** `{sub_v}`")
                else:
                    st.write(f"- **{key}:** `{val}`")


def render_history_page() -> None:
    """Render the functional session history page with filtering and detail inspection."""
    history_svc: HistoryService = st.session_state.history_service

    # Check if user selected a specific session to inspect
    selected_id = st.session_state.get("selected_history_session_id")
    if selected_id:
        render_historical_session_detail(selected_id)
        return

    st.markdown("## 📜 Practice Session History")
    st.caption("Review previous simulation attempts, conversation transcripts, evaluation scores, and explainable feedback.")

    # Filter & Search Controls
    with st.expander("🔍 Filter & Sort History Records", expanded=False):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            mode_filter = st.selectbox("Practice Mode", ["All"] + PRACTICE_MODES, index=0)
        with f_col2:
            diff_filter = st.selectbox("Difficulty Tier", ["All"] + DIFFICULTY_LEVELS, index=0)
        with f_col3:
            min_score = st.slider("Minimum Score", min_value=0, max_value=100, value=0, step=5)
        with f_col4:
            sort_order = st.selectbox(
                "Sort By",
                ["completed_at DESC", "completed_at ASC", "overall_score DESC", "overall_score ASC"],
                format_func=lambda x: {
                    "completed_at DESC": "Date: Most Recent",
                    "completed_at ASC": "Date: Oldest First",
                    "overall_score DESC": "Score: Highest First",
                    "overall_score ASC": "Score: Lowest First",
                }[x],
            )

        st.markdown("**📅 Date Range Filter (Optional)**")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            hist_start_date = st.date_input("From Date", value=None, key="history_start_date")
        with d_col2:
            hist_end_date = st.date_input("To Date", value=None, key="history_end_date")

    start_date_iso = f"{hist_start_date.isoformat()}T00:00:00" if hist_start_date else None
    end_date_iso = f"{hist_end_date.isoformat()}T23:59:59" if hist_end_date else None

    sessions = history_svc.list_sessions(
        mode=mode_filter if mode_filter != "All" else None,
        difficulty=diff_filter if diff_filter != "All" else None,
        start_date=start_date_iso,
        end_date=end_date_iso,
        min_score=float(min_score) if min_score > 0 else None,
        order_by=sort_order,
    )

    if not sessions:
        st.markdown(
            """
            <div class="banner-demo">
                <strong>ℹ️ No Practice Records Found</strong><br>
                No completed practice sessions match your selected filters. Practice a simulation scenario in the 
                <strong>Practice</strong> tab and evaluate performance to automatically record historical data.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"**Showing {len(sessions)} recorded practice session{'s' if len(sessions) != 1 else ''}**")

    for s in sessions:
        mode_icon = MODE_ICONS.get(s.mode, "🎙️")
        with st.container():
            st.markdown(
                f"""
                <div class="metric-card" style="margin-bottom: 12px; padding: 16px 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span class="mode-badge">{mode_icon} {s.mode}</span>
                            <span class="diff-badge">{s.difficulty}</span>
                            <h3 style="margin: 8px 0 4px 0;">{s.scenario_name}</h3>
                            <small style="color: #64748b;">Interviewer: <strong>{s.persona_name}</strong> • Completed: {s.formatted_date} • Turns: {s.turn_count} • Duration: {s.formatted_duration}</small>
                        </div>
                        <div style="text-align: right; min-width: 140px;">
                            <div style="font-size: 2.2rem; font-weight: 700; color: #1e40af;">{s.overall_score:.1f} <span style="font-size: 1rem; color: #64748b;">/ 100</span></div>
                            <small style="color: #475569;">Recorded Score</small>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_b1, col_b2 = st.columns([5, 1])
            with col_b1:
                if st.button(f"🔍 Inspect Report & Transcript", key=f"inspect_{s.session_id}", use_container_width=True):
                    st.session_state.selected_history_session_id = s.session_id
                    st.rerun()
            with col_b2:
                if st.button("🗑️ Delete", key=f"del_{s.session_id}", use_container_width=True):
                    history_svc.delete_session(s.session_id)
                    st.rerun()


def render_historical_session_detail(session_id: str) -> None:
    """Render the full detail view for an individual historical session."""
    history_svc: HistoryService = st.session_state.history_service
    session = history_svc.get_session(session_id)

    if not session:
        st.error("Historical session record not found.")
        if st.button("← Back to History List"):
            st.session_state.selected_history_session_id = None
            st.rerun()
        return

    if st.button("← Back to History List"):
        st.session_state.selected_history_session_id = None
        st.rerun()

    mode_icon = MODE_ICONS.get(session.mode, "🎙️")
    st.markdown(f"## {mode_icon} {session.scenario_name}")
    st.markdown(
        f"**Role-Play Simulation** with **{session.persona_name}** • "
        f"`{session.mode}` • `{session.difficulty}` • Completed: `{session.formatted_date}`"
    )

    # Historical Score Hero Card
    st.markdown(
        f"""
        <div class="score-hero-card">
            <h1 style="font-size: 3rem; margin: 0; color: #1e40af;">{session.overall_score:.1f} <span style="font-size: 1.5rem; color: #64748b;">/ {session.max_score:.0f}</span></h1>
            <p style="font-size: 1.15rem; margin-top: 8px; font-weight: 600; color: #1e293b;">Historical Overall Performance Score</p>
            <span class="mode-badge">{session.mode}</span>
            <span class="diff-badge">{session.difficulty}</span>
            <div style="margin-top: 8px; color: #475569; font-size: 0.9rem;">
                Turns: <strong>{session.turn_count}</strong> • Duration: <strong>{session.formatted_duration}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(min(1.0, max(0.0, session.overall_score / 100.0)))

    tab_eval, tab_feed, tab_transcript = st.tabs([
        "🏆 Evaluation Breakdown (Phase 5)",
        "💡 Explainable Feedback (Phase 6)",
        "📜 Conversation Transcript",
    ])

    with tab_eval:
        st.markdown("### 🏆 Phase 5 Evaluation Breakdown")
        st.caption("Dimensional scores, evidence, and rationale recorded at session completion.")

        if session.dimensions:
            for dim in session.dimensions:
                st.markdown(
                    f"""
                    <div class="dimension-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #1e40af;">{dim.name}</h4>
                            <span style="font-size: 1.2rem; font-weight: 700; color: #1e40af;">
                                {f"{dim.score:.1f} / 100" if dim.score is not None else "Not Evaluated"}
                            </span>
                        </div>
                        <p style="margin: 6px 0; font-size: 0.92rem; color: #334155;"><strong>Rationale:</strong> {dim.rationale}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if dim.evidence:
                    with st.expander(f"Evidence for {dim.name}", expanded=False):
                        for ev in dim.evidence:
                            st.write(f"- {ev}")
        elif session.evaluation and session.evaluation.dimensions:
            for dim in session.evaluation.dimensions:
                st.markdown(
                    f"""
                    <div class="dimension-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #1e40af;">{dim.name}</h4>
                            <span style="font-size: 1.2rem; font-weight: 700; color: #1e40af;">{dim.score:.1f} / 100</span>
                        </div>
                        <p style="margin: 6px 0; font-size: 0.92rem; color: #334155;"><strong>Rationale:</strong> {dim.rationale}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No detailed dimensional scores recorded.")

    with tab_feed:
        st.markdown("### 💡 Explainable Feedback (Phase 6)")
        st.caption("Saved WHAT / WHY / EVIDENCE / IMPACT / ACTION feedback guidance.")

        if session.feedback:
            if session.feedback.overall_summary:
                st.markdown(
                    f"""
                    <div class="feedback-card" style="border-left: 4px solid #3b82f6;">
                        <h4 style="margin: 0 0 6px 0; color: #1e40af;">💡 Executive Feedback Summary</h4>
                        <p style="margin: 0; font-size: 0.98rem; line-height: 1.5;">{session.feedback.overall_summary}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if session.feedback.priority_actions:
                st.markdown("#### 🎯 Priority Practice Actions")
                action_cols = st.columns(min(len(session.feedback.priority_actions), 3))
                for i, act in enumerate(session.feedback.priority_actions[:3]):
                    badge_cls = (
                        "badge-priority-high"
                        if act.priority == "High Priority"
                        else ("badge-priority-med" if act.priority == "Medium Priority" else "badge-priority-low")
                    )
                    with action_cols[i % len(action_cols)]:
                        st.markdown(
                            f"""
                            <div class="feedback-card" style="height: 100%;">
                                <span class="{badge_cls}">{act.priority}</span>
                                <h4 style="margin: 8px 0 6px 0; font-size: 1.05rem;">{act.title}</h4>
                                <div class="action-callout">
                                    <strong>Guideline:</strong> {act.action}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            col_str, col_imp = st.columns(2)
            with col_str:
                st.markdown("#### 🌟 Evidence-Backed Strengths")
                for s in session.feedback.strengths:
                    s_evi = format_evidence_display(s.evidence, evidence_type=s.evidence_type, source_reference=s.source_reference)
                    st.markdown(
                        f"""
                        <div class="strength-item" style="margin-bottom: 12px; padding: 12px 14px;">
                            <h4 style="margin: 0 0 4px 0; color: #065f46;">✓ {s.title}</h4>
                            <p style="margin: 0 0 4px 0; font-size: 0.9rem;"><strong>WHAT:</strong> {s.what}</p>
                            <p style="margin: 0 0 4px 0; font-size: 0.85rem; color: #047857;"><strong>EVIDENCE:</strong> <em>{s_evi}</em></p>
                            <p style="margin: 0; font-size: 0.85rem; color: #475569;"><strong>IMPACT:</strong> {s.impact}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with col_imp:
                st.markdown("#### 📈 Key Actionable Improvements")
                for imp in session.feedback.improvements:
                    badge_cls = (
                        "badge-priority-high"
                        if imp.priority == "High Priority"
                        else ("badge-priority-med" if imp.priority == "Medium Priority" else "badge-priority-low")
                    )
                    imp_evi = format_evidence_display(imp.evidence, evidence_type=imp.evidence_type, source_reference=imp.source_reference)
                    st.markdown(
                        f"""
                        <div class="improve-item" style="margin-bottom: 12px; padding: 12px 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <h4 style="margin: 0; color: #92400e;">⚡ {imp.title}</h4>
                                <span class="{badge_cls}">{imp.priority}</span>
                            </div>
                            <p style="margin: 0 0 4px 0; font-size: 0.9rem;"><strong>WHAT:</strong> {imp.what}</p>
                            <p style="margin: 0 0 4px 0; font-size: 0.85rem; color: #92400e;"><strong>WHY:</strong> {imp.why}</p>
                            <p style="margin: 0 0 6px 0; font-size: 0.85rem; color: #475569;"><strong>EVIDENCE:</strong> <em>{imp_evi}</em></p>
                            <div class="action-callout" style="margin-top: 4px; padding: 8px 10px;">
                                <strong style="color: #1e40af;">ACTION:</strong> {imp.action}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        elif session.evaluation:
            col_str, col_imp = st.columns(2)
            with col_str:
                st.markdown("#### 🌟 Strengths")
                for s in session.evaluation.strengths:
                    st.markdown(f'<div class="strength-item">✓ {s}</div>', unsafe_allow_html=True)
            with col_imp:
                st.markdown("#### 📈 Improvement Areas")
                for imp in session.evaluation.improvement_areas:
                    st.markdown(f'<div class="improve-item">⚡ {imp}</div>', unsafe_allow_html=True)
        else:
            st.info("No explainable feedback stored for this session.")

    with tab_transcript:
        st.markdown("### 📜 Conversation Transcript")
        st.caption("Verbatim dialogue between candidate and AI persona. Internal system instructions are strictly excluded.")

        user_facing_msgs = session.user_facing_messages()
        if not user_facing_msgs:
            st.info("No conversation messages recorded for this session.")
        else:
            for msg in user_facing_msgs:
                if msg.role == "assistant":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(f"**{session.persona_name}**")
                        st.markdown(msg.content)
                elif msg.role == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.markdown("**You**")
                        st.markdown(msg.content)


def render_analytics_page() -> None:
    """Render the longitudinal performance analytics and session comparison page."""
    analytics_svc: AnalyticsService = st.session_state.analytics_service
    history_svc: HistoryService = st.session_state.history_service

    st.markdown("## 📊 Performance Analytics & Progress")
    st.caption("Descriptive statistics, longitudinal trends, recurring patterns, and neutral session comparisons.")

    # Filter Controls
    with st.expander("🔍 Filter Analytics Scope", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            mode_filter = st.selectbox("Practice Mode", ["All"] + PRACTICE_MODES, key="analytics_mode_filter")
        with c2:
            diff_filter = st.selectbox("Difficulty Tier", ["All"] + DIFFICULTY_LEVELS, key="analytics_diff_filter")

        st.markdown("**📅 Date Range Filter (Optional)**")
        ad_col1, ad_col2 = st.columns(2)
        with ad_col1:
            ana_start_date = st.date_input("From Date", value=None, key="analytics_start_date")
        with ad_col2:
            ana_end_date = st.date_input("To Date", value=None, key="analytics_end_date")

    ana_start_iso = f"{ana_start_date.isoformat()}T00:00:00" if ana_start_date else None
    ana_end_iso = f"{ana_end_date.isoformat()}T23:59:59" if ana_end_date else None

    sessions = analytics_svc.get_sessions(
        mode=mode_filter if mode_filter != "All" else None,
        difficulty=diff_filter if diff_filter != "All" else None,
        start_date=ana_start_iso,
        end_date=ana_end_iso,
    )

    if not sessions:
        st.markdown(
            """
            <div class="banner-demo">
                <strong>ℹ️ No Practice Data for Analytics</strong><br>
                Complete practice sessions to unlock longitudinal trends, dimension breakdowns, recurring patterns, and comparisons.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # High-level KPIs
    summary = analytics_svc.get_overall_summary(sessions)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    with kpi_col1:
        st.metric("Completed Sessions", summary["total_sessions"])
    with kpi_col2:
        st.metric("Average Score", f"{summary['average_score']:.1f} / 100")
    with kpi_col3:
        st.metric("Highest Recorded Score", f"{summary['highest_recorded_score']:.1f}")
    with kpi_col4:
        st.metric("Lowest Recorded Score", f"{summary['lowest_recorded_score']:.1f}")
    with kpi_col5:
        st.metric("Average Turns", f"{summary['average_turns']:.1f}")

    st.markdown("---")

    # Longitudinal Progress Trend
    st.markdown("### 📈 Chronological Score Progression")
    progress_data = analytics_svc.get_chronological_progress(sessions)

    if len(progress_data) < 2:
        st.info(
            "ℹ️ **1 practice session recorded.** Complete at least two practice sessions to display a chronological trend line."
        )
    else:
        # Build simple chart dictionary
        chart_data = {
            f"#{p['session_number']} {p['scenario'][:16]}...": p["score"]
            for p in progress_data
        }
        st.line_chart(chart_data)

    st.markdown("---")

    # Mode & Difficulty Breakdowns
    col_mb, col_db = st.columns(2)
    with col_mb:
        st.markdown("### 👔 Mode Performance Breakdown")
        mode_stats = analytics_svc.get_mode_breakdown(sessions)
        if mode_stats:
            for ms in mode_stats:
                st.markdown(
                    f"""
                    <div class="metric-card" style="padding: 12px 16px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>{MODE_ICONS.get(ms['mode'], '🎙️')} {ms['mode']}</strong>
                            <span style="font-weight: 700; color: #1e40af;">Avg: {ms['average_score']:.1f}</span>
                        </div>
                        <small style="color: #64748b;">Sessions: {ms['session_count']} • Range: {ms['lowest_score']:.1f} – {ms['highest_score']:.1f}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No mode-specific records found.")

    with col_db:
        st.markdown("### 🎯 Difficulty Tier Breakdown")
        diff_stats = analytics_svc.get_difficulty_breakdown(sessions)
        if diff_stats:
            for ds in diff_stats:
                st.markdown(
                    f"""
                    <div class="metric-card" style="padding: 12px 16px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>{ds['difficulty']}</strong>
                            <span style="font-weight: 700; color: #1e40af;">Avg: {ds['average_score']:.1f}</span>
                        </div>
                        <small style="color: #64748b;">Sessions: {ds['session_count']} • Range: {ds['lowest_score']:.1f} – {ds['highest_score']:.1f}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No difficulty breakdown records found.")

    st.markdown("---")

    # Dimension Historical Averages
    st.markdown("### 📊 Historical Dimension Averages")
    st.caption("Descriptive averages across all evaluated dimensions.")
    dim_stats = analytics_svc.get_dimension_averages(sessions)
    if dim_stats:
        dim_cols = st.columns(min(len(dim_stats), 3))
        for idx, ds in enumerate(dim_stats):
            with dim_cols[idx % len(dim_cols)]:
                st.markdown(
                    f"""
                    <div class="dimension-card" style="padding: 12px 16px; margin-bottom: 8px;">
                        <h4 style="margin: 0; color: #1e40af; font-size: 1rem;">{ds['dimension']}</h4>
                        <div style="font-size: 1.6rem; font-weight: 700; color: #1e40af; margin: 4px 0;">
                            {ds['average_score']:.1f} <span style="font-size: 0.85rem; color: #64748b;">/ 100</span>
                        </div>
                        <small style="color: #64748b;">Evaluated in {ds['evaluations_count']} session{'s' if ds['evaluations_count'] != 1 else ''}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No dimensional score records found.")

    st.markdown("---")

    # Recurring Patterns (Improvements & Strengths)
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("### 📈 Recurring Improvement Themes")
        st.caption("Frequently observed actionable areas across stored sessions.")
        improvements = analytics_svc.get_recurring_improvements(sessions)
        if improvements:
            for imp in improvements:
                st.markdown(
                    f"""
                    <div class="improve-item" style="padding: 10px 14px; margin-bottom: 8px;">
                        <strong>⚡ {imp['theme']}</strong><br>
                        <small style="color: #475569;">{imp['description']} ({imp['percentage']}% of sessions)</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No recurring improvement patterns detected yet.")

    with col_p2:
        st.markdown("### 🌟 Frequently Observed Strengths")
        st.caption("Verifiable competencies consistently demonstrated across sessions.")
        strengths = analytics_svc.get_recurring_strengths(sessions)
        if strengths:
            for st_item in strengths:
                st.markdown(
                    f"""
                    <div class="strength-item" style="padding: 10px 14px; margin-bottom: 8px;">
                        <strong>✓ {st_item['strength']}</strong><br>
                        <small style="color: #475569;">{st_item['description']} ({st_item['percentage']}% of sessions)</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No recurring strength patterns detected yet.")

    st.markdown("---")

    # Two-Session Comparison Tool
    st.markdown("### ⚖️ Side-by-Side Session Comparison")
    st.caption("Select any two completed sessions to compare scores, dimensions, and feedback side-by-side.")

    all_sessions = history_svc.list_sessions(order_by="completed_at DESC")
    if len(all_sessions) < 2:
        st.info("ℹ️ At least two completed practice sessions are required to perform a comparison.")
    else:
        session_options = {
            f"{s.formatted_date} — {s.scenario_name} ({s.mode}, Score: {s.overall_score:.1f})": s.session_id
            for s in all_sessions
        }
        labels = list(session_options.keys())

        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            choice_a = st.selectbox("Baseline Session (Session A)", labels, index=1 if len(labels) > 1 else 0)
        with col_comp2:
            choice_b = st.selectbox("Comparison Session (Session B)", labels, index=0)

        id_a = session_options[choice_a]
        id_b = session_options[choice_b]

        if id_a == id_b:
            st.warning("Please select two distinct sessions to compare.")
        else:
            sess_a = history_svc.get_session(id_a)
            sess_b = history_svc.get_session(id_b)
            if sess_a and sess_b:
                comp = compare_sessions(sess_a, sess_b)

                # Score Delta Hero Callout
                score_delta = comp["overall_score_difference"]
                delta_color = "#10b981" if score_delta > 0 else ("#ef4444" if score_delta < 0 else "#64748b")
                st.markdown(
                    f"""
                    <div class="metric-card" style="text-align: center; border-left: 5px solid {delta_color};">
                        <h4 style="margin: 0; color: #1e293b;">{comp['overall_score_description']}</h4>
                        <div style="font-size: 2.4rem; font-weight: 700; color: {delta_color}; margin: 8px 0;">
                            {score_delta:+.1f} Points
                        </div>
                        <small style="color: #64748b;">
                            Session A ({comp['session_a']['date']}): <strong>{comp['session_a']['overall_score']:.1f}</strong> ➔ 
                            Session B ({comp['session_b']['date']}): <strong>{comp['session_b']['overall_score']:.1f}</strong>
                        </small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if sess_a.mode != sess_b.mode or sess_a.scenario_id != sess_b.scenario_id:
                    st.caption(
                        "ℹ️ *Note: Selected sessions represent different practice modes or scenarios. "
                        "Recorded score differences reflect differing competency rubrics and scenario expectations "
                        "rather than an assessment of change in candidate ability.*"
                    )

                # Metadata Comparison
                st.markdown("#### 📋 Session Metadata Comparison")
                c_meta1, c_meta2 = st.columns(2)
                with c_meta1:
                    st.markdown(
                        f"""
                        **Session A (Baseline):**
                        - **Scenario:** {comp['session_a']['scenario']}
                        - **Mode:** {comp['session_a']['mode']}
                        - **Difficulty:** {comp['session_a']['difficulty']}
                        - **Interviewer:** {comp['session_a']['persona']}
                        - **Turns:** {comp['session_a']['turn_count']}
                        - **Duration:** {comp['session_a']['duration']}
                        """
                    )
                with c_meta2:
                    st.markdown(
                        f"""
                        **Session B (Comparison):**
                        - **Scenario:** {comp['session_b']['scenario']}
                        - **Mode:** {comp['session_b']['mode']}
                        - **Difficulty:** {comp['session_b']['difficulty']}
                        - **Interviewer:** {comp['session_b']['persona']}
                        - **Turns:** {comp['session_b']['turn_count']}
                        - **Duration:** {comp['session_b']['duration']}
                        """
                    )

                # Dimensional Differences
                st.markdown("#### 📊 Dimensional Score Comparisons")
                dim_comps = comp["dimension_comparisons"]
                for dc in dim_comps:
                    sc_a = f"{dc['score_a']:.1f}" if dc['score_a'] is not None else "N/A"
                    sc_b = f"{dc['score_b']:.1f}" if dc['score_b'] is not None else "N/A"
                    diff_val = dc['difference']
                    diff_color = "#10b981" if diff_val and diff_val > 0 else ("#ef4444" if diff_val and diff_val < 0 else "#64748b")

                    st.markdown(
                        f"""
                        <div class="dimension-card" style="padding: 10px 14px; margin-bottom: 6px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>{dc['dimension']}</strong>
                                <div>
                                    <span style="color: #64748b;">Session A: {sc_a}</span> &nbsp;|&nbsp;
                                    <span style="color: #1e40af;">Session B: {sc_b}</span> &nbsp;|&nbsp;
                                    <span style="font-weight: 700; color: {diff_color};">Diff: {dc['difference_display']}</span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Common & Distinct Strengths/Improvements
                col_cs, col_ci = st.columns(2)
                with col_cs:
                    st.markdown("#### 🌟 Strength Patterns")
                    if comp["common_strengths"]:
                        st.write("**Demonstrated in both sessions:**")
                        for s in comp["common_strengths"]:
                            st.write(f"- ✓ {s}")
                    if comp["distinct_b_strengths"]:
                        st.write("**New in Session B:**")
                        for s in comp["distinct_b_strengths"]:
                            st.write(f"- 🌟 {s}")

                with col_ci:
                    st.markdown("#### 📈 Improvement Patterns")
                    if comp["common_improvements"]:
                        st.write("**Shared across both sessions:**")
                        for imp in comp["common_improvements"]:
                            st.write(f"- ⚡ {imp}")
                    if comp["distinct_b_improvements"]:
                        st.write("**Specific to Session B:**")
                        for imp in comp["distinct_b_improvements"]:
                            st.write(f"- 🔍 {imp}")


def render_settings_page(ai_provider) -> None:
    """Render the application configuration and provider settings page."""
    st.markdown("## ⚙️ Application Settings")
    st.caption("Inspect application metadata, AI provider connectivity, and persistent storage configuration.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📱 Application Metadata")
        st.markdown(
            f"""
            - **Application:** `{APP_NAME}`
            - **Subtitle:** `{APP_SUBTITLE}`
            - **Version:** `{APP_VERSION}`
            - **Current Phase:** `Phase 7 — Session History & Analytics`
            - **Architecture:** Modular Python / Streamlit
            """
        )

    with col2:
        st.markdown("### 🤖 AI Provider Status")
        status = ai_provider.get_status()
        st.markdown(
            f"""
            - **Provider Mode:** `{status.name}`
            - **Connection Status:** `{'Connected' if status.is_connected else 'Demo Mode (Not Connected)'}`
            - **Active Model:** `{status.model_name}`
            - **Details:** {status.status_message}
            """
        )

    st.markdown("---")
    st.markdown("### 🗄️ Local Persistent Storage (SQLite)")
    history_svc: HistoryService = st.session_state.history_service
    session_count = history_svc.count_sessions()
    db_path = getattr(history_svc.repository, "db_path", DEFAULT_DB_PATH)

    st.markdown(
        f"""
        - **Storage Engine:** `SQLite (Python Standard Library)`
        - **Database Path:** `{db_path}`
        - **Total Saved Sessions:** `{session_count}`
        - **Privacy Guarantee:** All conversational transcripts, scores, and feedback records remain on your local machine. 
          No conversation data is transmitted to external database servers or tracked externally.
        """
    )

    with st.expander("⚠️ Storage Maintenance / Clear History"):
        st.warning("Clearing history will permanently remove all stored practice sessions and analytics.")
        confirm_clear = st.checkbox("I understand and wish to clear all historical records.")
        if confirm_clear:
            if st.button("🗑️ Permanently Clear History", type="secondary"):
                history_svc.clear_all()
                st.success("All session history successfully cleared.")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🔑 API Configuration & Security")
    st.markdown(
        """
        In accordance with security best practices:
        - **Pitch Practice Partner operates in Demo Mode by default without requiring an API key.**
        - To connect a live LLM endpoint, configure your environment variables in `.env`.
        - Secrets and keys are never hard-coded or logged in plaintext.
        """
    )

    with st.expander("📄 Environment Configuration Template (.env.example)"):
        st.code(
            """# Pitch Practice Partner - Environment Configuration
AI_PROVIDER=openai  # Supported: demo, openai, gemini, anthropic
AI_API_KEY=your_api_key_here
AI_MODEL=gpt-4o-mini
""",
            language="bash",
        )



def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title=f"{APP_NAME} — {APP_SUBTITLE}",
        page_icon="🎙️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()

    scenario_mgr: ScenarioManager = st.session_state.scenario_manager
    ai_provider = st.session_state.ai_provider

    render_sidebar()

    current_page = st.session_state.nav_page
    if current_page == "Home":
        render_home_page(scenario_mgr)
    elif current_page == "Practice":
        render_practice_page(scenario_mgr)
    elif current_page == "History":
        render_history_page()
    elif current_page == "Analytics":
        render_analytics_page()
    elif current_page == "Settings":
        render_settings_page(ai_provider)
    else:
        render_home_page(scenario_mgr)


if __name__ == "__main__":
    main()
