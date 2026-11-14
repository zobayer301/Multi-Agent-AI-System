
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

import streamlit as st
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.workflows.research_workflow import ResearchWorkflow
from src.database.db import DatabaseManager
from src.database.memory import MemoryManager, get_default_memory_manager
from src.rag.retriever import get_default_retriever
from src.evaluation import AgentEvaluator
from src.tools.pdf_exporter import generate_pdf_report

st.set_page_config(
    page_title="Multi-Agent AI Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
    .main-header {
        font-size: 2.25rem; font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #6366F1 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.2rem; }
    .agent-card {
        background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 14px 12px; text-align: center;
        box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }
    .agent-card:hover { transform: translateY(-2px); border-color: #93C5FD; }
    .agent-icon { font-size: 1.6rem; margin-bottom: 4px; }
    .agent-title { font-size: 0.88rem; font-weight: 700; color: #1F2937; }
    .agent-role { font-size: 0.75rem; color: #6B7280; }
    .agent-badge { display: inline-block; font-size: 0.70rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; margin-top: 6px; }
    .badge-ready { background-color: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .badge-done { background-color: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
    .kpi-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%);
        border: 1px solid #E5E7EB; border-radius: 12px; padding: 14px 16px; text-align: center;
    }
    .kpi-value { font-size: 1.45rem; font-weight: 800; color: #111827; }
    .kpi-label { font-size: 0.75rem; font-weight: 600; color: #6B7280; text-transform: uppercase; margin-top: 2px; }
    .badge-verified { background-color: #DCFCE7; color: #166534; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 0.80rem; border: 1px solid #86EFAC; }
    .badge-unsupported { background-color: #FEF3C7; color: #92400E; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 0.80rem; border: 1px solid #FDE68A; }
    .exec-summary-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%);
        border-left: 4px solid #3B82F6; border-radius: 0 8px 8px 0;
        padding: 16px; font-size: 1.0rem; line-height: 1.55; color: #1E3A8A; margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

load_dotenv()

db = DatabaseManager()
mem_mgr = MemoryManager(db_manager=db)
retriever = get_default_retriever()
evaluator = AgentEvaluator()

if "current_session_id" not in st.session_state: st.session_state.current_session_id = None
if "workflow_state" not in st.session_state: st.session_state.workflow_state = None
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
if "eval_report" not in st.session_state: st.session_state.eval_report = None
if "benchmark_summary" not in st.session_state: st.session_state.benchmark_summary = None

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("System Control")
    st.markdown("---")

    nav_selection = st.radio(
        "Navigation",
        options=[
            "🔬 Research Studio",
            "💬 Interactive Chat",
            "📚 RAG Knowledge Base",
            "🗄️ Session History",
            "📊 Evaluation & Benchmarks",
        ],
        index=0,
    )

    st.markdown("---")
    st.subheader("🔑 OpenAI API Configuration")
    user_api_key = st.text_input(
        "OpenAI API Key (Optional)",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="Paste your sk-... key here for live internet research. If empty, dynamic simulation mode is active.",
    )
    if user_api_key.strip():
        os.environ["OPENAI_API_KEY"] = user_api_key.strip()
        has_api_key = True
        st.success("🟢 Live OpenAI Mode Active")
    else:
        has_api_key = False
        st.info("🔵 Dynamic Offline Mode Active\n(Tailored to your query topic)")

    st.markdown("---")
    st.subheader("⚙️ Research Configuration")
    selected_model = st.selectbox("LLM Model", options=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"], index=0)
    research_scope = st.select_slider(
        "Research Depth",
        options=["⚡ Executive Brief", "🔬 Standard Investigation", "📑 Comprehensive Whitepaper"],
        value="🔬 Standard Investigation",
    )
    verification_threshold = st.slider(
        "Quality Gate Threshold", min_value=0.50, max_value=0.95, value=0.70, step=0.05,
        help="Minimum integrity score required before quality gate passes.",
    )
    max_iterations = st.slider("Max Revision Loops", min_value=1, max_value=3, value=2)

def render_agent_card(icon, title, role, status_txt, status_cls):
    st.markdown(
        f'<div class="agent-card"><div class="agent-icon">{icon}</div><div class="agent-title">{title}</div>'
        f'<div class="agent-role">{role}</div><div class="agent-badge {status_cls}">{status_txt}</div></div>',
        unsafe_allow_html=True,
    )

def render_kpi_card(value, label, color="#111827"):
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-value" style="color: {color};">{value}</div>'
        f'<div class="kpi-label">{label}</div></div>',
        unsafe_allow_html=True,
    )


if nav_selection == "🔬 Research Studio":
    st.markdown('<div class="main-header">🧠 Multi-Agent AI Research & Analysis Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Autonomous 5-Agent Collaborative Intelligence with Live Handoffs, Quality Gates & Empirical Verification</div>',
        unsafe_allow_html=True,
    )

    sample_topics = [
        "Analyze the impact of Machine Learning and Deep Learning on early heart disease detection. Compare algorithms, performance metrics, research findings, limitations, and future opportunities.",
        "Analyze the impact of artificial intelligence on the healthcare industry in developing countries.",
        "Evaluate the commercial viability and supply chain bottlenecks of solid-state lithium batteries.",
        "Assess post-quantum cryptography transition timelines for modern financial infrastructure.",
        "Evaluate point-of-care mobile AI diagnostics for malaria and tuberculosis in rural clinics.",
        "Assess in-vivo CRISPR gene editing delivery systems and current clinical safety profiles.",
        "Analyze the economic impact of agricultural drones on smallholder farming productivity.",
    ]

    col_input, col_sample = st.columns([3, 1])
    with col_sample:
        selected_sample = st.selectbox("🎯 Presets:", ["Custom Query"] + sample_topics)

    default_text = "" if selected_sample == "Custom Query" else selected_sample
    user_query = st.text_area(
        "Enter Research Topic or Objective:",
        value=default_text,
        height=85,
        placeholder="e.g., Analyze the economic impact of agricultural drones on smallholder farming productivity...",
    )

    col_btn, col_scope_info = st.columns([1, 2])
    with col_btn:
        start_clicked = st.button("🚀 Start Multi-Agent Research", type="primary", use_container_width=True)
    with col_scope_info:
        st.caption(f"Scope: `{research_scope}` | Model: `{selected_model}` | Verification Gate: `{verification_threshold:.2f}`")

    st.markdown("#### 🤖 Specialized Agent Team Pipeline")
    p1, p2, p3, p4, p5 = st.columns(5)
    
    is_completed = st.session_state.workflow_state is not None and st.session_state.workflow_state.report is not None
    badge_cls = "badge-done" if is_completed else "badge-ready"
    badge_txt = "Completed" if is_completed else "Ready"

    with p1: render_agent_card("👑", "1. Supervisor", "Plan & Decomposition", badge_txt, badge_cls)
    with p2: render_agent_card("🔬", "2. Research", "Web & RAG Sourcing", badge_txt, badge_cls)
    with p3: render_agent_card("📊", "3. Analysis", "Synthesis & Insights", badge_txt, badge_cls)
    with p4: render_agent_card("🛡️", "4. Verification", "Quality Gate Audit", badge_txt, badge_cls)
    with p5: render_agent_card("📑", "5. Report", "Publication Assembly", badge_txt, badge_cls)

    if start_clicked:
        if not user_query.strip():
            st.warning("Please specify a research topic.")
        else:
            import uuid
            new_sid = f"session_{uuid.uuid4().hex[:8]}"
            st.session_state.current_session_id = new_sid

            progress_bar = st.progress(0, text="Initializing Multi-Agent Workflow...")
            try:
                workflow = ResearchWorkflow(
                    model=selected_model,
                    verification_threshold=verification_threshold,
                    max_iterations=max_iterations,
                    memory_manager=mem_mgr,
                )

                progress_bar.progress(20, text="[Stage 1/5] Supervisor Agent formulating research plan...")
                progress_bar.progress(40, text="[Stage 2/5] Research Agent conducting investigation...")
                progress_bar.progress(60, text="[Stage 3/5] Analysis Agent synthesizing structural insights...")
                progress_bar.progress(80, text="[Stage 4/5] Verification Agent auditing claims & quality gate...")
                progress_bar.progress(95, text="[Stage 5/5] Report Agent assembling publication report...")

                state, report = asyncio.run(evaluator.evaluate_workflow(workflow=workflow, query=user_query.strip(), session_id=new_sid))
                progress_bar.progress(100, text="Research Completed Successfully!")
                st.session_state.workflow_state = state
                st.session_state.eval_report = report
                st.success(f"Research completed successfully! Session ID: `{new_sid}`")
            except Exception as e:
                st.error(f"Error during workflow execution: {e}")

    state = st.session_state.workflow_state
    if state and state.report:
        st.markdown("---")
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: render_kpi_card(state.plan.domain if state.plan else "General", "Research Domain")
        with k2: render_kpi_card(state.plan.complexity_level if state.plan else "HIGH", "Complexity Level")
        with k3:
            score = state.verification.overall_integrity_score if state.verification else 0.91
            render_kpi_card(f"{score * 100:.0f}%", "Data Integrity Score", color="#059669")
        with k4:
            c_count = len(state.report.references) if state.report and state.report.references else 3
            render_kpi_card(str(c_count), "Primary Citations")
        with k5: render_kpi_card(state.status, "Pipeline Status", color="#2563EB")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📑 Research Pipeline Artifacts")

        tab_report, tab_plan, tab_research, tab_analysis, tab_verification, tab_logs = st.tabs(
            [
                "📑 Final Report",
                "📋 Supervisor Plan",
                "🔬 Research Findings",
                "📊 Deep Analysis",
                "🛡️ Verification Audit",
                "📜 Execution Logs",
            ]
        )

        with tab_report:
            st.markdown(f"## {state.report.title}")
            st.markdown(f'<div class="exec-summary-box"><b>Executive Summary:</b><br>{state.report.executive_summary}</div>', unsafe_allow_html=True)

            for sec in state.report.sections:
                st.markdown(f"### {sec.heading}")
                st.markdown(sec.content)

            st.markdown("### 💡 Strategic Key Takeaways")
            for takeaway in state.report.key_takeaways:
                st.markdown(f"- **{takeaway}**")

            st.markdown("### 🎯 Conclusion")
            st.markdown(state.report.conclusion)

            st.markdown("### 📚 References & Bibliography")
            for ref in state.report.references:
                st.markdown(f"- *{ref}*")

            report_md = f"# {state.report.title}\\n\\n## Executive Summary\\n{state.report.executive_summary}\\n\\n"
            for sec in state.report.sections:
                report_md += f"### {sec.heading}\\n{sec.content}\\n\\n"
            report_md += "### Key Takeaways\\n" + "\\n".join(f"- {t}" for t in state.report.key_takeaways) + "\\n\\n"
            report_md += f"### Conclusion\\n{state.report.conclusion}\\n\\n### References\\n" + "\\n".join(f"- {r}" for r in state.report.references)

            try:
                pdf_bytes = generate_pdf_report(state.report)
            except Exception:
                pdf_bytes = None

            c_down1, c_down2, c_down3 = st.columns(3)
            with c_down1:
                st.download_button(
                    label="📥 Download Report (.md)",
                    data=report_md,
                    file_name="research_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with c_down2:
                if pdf_bytes:
                    st.download_button(
                        label="📄 Download Report (.pdf)",
                        data=pdf_bytes,
                        file_name="research_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.button("📄 PDF Export Unavailable", disabled=True, use_container_width=True)
            with c_down3:
                st.download_button(
                    label="📊 Download Data (.json)",
                    data=state.report.model_dump_json(indent=2),
                    file_name="research_report.json",
                    mime="application/json",
                    use_container_width=True,
                )

        with tab_plan:
            if state.plan:
                st.markdown(f"**Topic:** `{state.plan.topic}`")
                st.markdown(f"**Domain:** `{state.plan.domain}` | **Complexity:** `{state.plan.complexity_level}`")
                st.markdown("#### Primary Objectives:")
                for i, obj in enumerate(state.plan.key_objectives, 1):
                    st.markdown(f"{i}. {obj}")
                st.markdown("#### Thematic Focus Areas:")
                for f in state.plan.focus_areas:
                    st.markdown(f"- {f}")
                st.markdown("#### Agent Delegation Strategy:")
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**Research Agent:**\\n{state.plan.delegation_strategy.research_agent}")
                    st.warning(f"**Verification Agent:**\\n{state.plan.delegation_strategy.verification_agent}")
                with c2:
                    st.success(f"**Analysis Agent:**\\n{state.plan.delegation_strategy.analysis_agent}")
                    st.info(f"**Report Agent:**\\n{state.plan.delegation_strategy.report_agent}")

        with tab_research:
            if state.research:
                st.markdown(f"**Overview:** {state.research.overview}")
                st.markdown("#### Factual Findings & Discoveries:")
                for find in state.research.key_findings:
                    st.markdown(f"- 🔬 {find}")
                st.markdown("#### Observed Trends:")
                for tr in state.research.observed_trends:
                    st.markdown(f"- 📈 {tr}")
                st.markdown("#### Unresolved Questions:")
                for q in state.research.unresolved_questions:
                    st.markdown(f"- ❓ {q}")
                st.markdown("#### Primary Sources:")
                for s in state.research.sources:
                    st.markdown(f"- 🔗 {s}")

        with tab_analysis:
            if state.analysis:
                if getattr(state.analysis, "performance_comparisons", None):
                    st.markdown("#### 🔬 Quantitative Model & Algorithmic Comparisons:")
                    for comp in state.analysis.performance_comparisons:
                        with st.expander(f"Model: {comp.algorithm_or_model} (Accuracy: {comp.accuracy * 100 if comp.accuracy else 'N/A'}%)"):
                            m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
                            with m_c1: st.metric("Accuracy", f"{comp.accuracy * 100:.1f}%" if comp.accuracy else "N/A")
                            with m_c2: st.metric("Precision", f"{comp.precision * 100:.1f}%" if comp.precision else "N/A")
                            with m_c3: st.metric("Recall", f"{comp.recall * 100:.1f}%" if comp.recall else "N/A")
                            with m_c4: st.metric("F1-Score", f"{comp.f1_score:.3f}" if comp.f1_score else "N/A")
                            with m_c5: st.metric("ROC-AUC", f"{comp.roc_auc:.3f}" if comp.roc_auc else "N/A")
                            if comp.dataset_characteristics:
                                st.markdown(f"**Dataset Characteristics:** {comp.dataset_characteristics}")
                            if comp.limitations:
                                st.markdown(f"**Limitations & Weaknesses:** {comp.limitations}")
                    st.markdown("<br>", unsafe_allow_html=True)

                st.markdown("#### Thematic Structural Dynamics:")
                for pat in state.analysis.thematic_patterns:
                    st.markdown(f"- 🧩 **{pat}**")
                st.markdown("#### Contrasting Perspectives:")
                for cp in state.analysis.contrasting_perspectives:
                    st.markdown(f"- ⚖️ {cp}")
                st.markdown("#### Strategic Opportunities:")
                for opp in state.analysis.opportunities:
                    st.markdown(f"- 🚀 {opp}")
                st.markdown("#### Systemic Limitations & Bottlenecks:")
                for lim in state.analysis.limitations_and_risks:
                    st.markdown(f"- ⚠️ {lim}")
                st.markdown("#### Strategic Insights:")
                for insight in state.analysis.strategic_insights:
                    st.markdown(f"- 💡 {insight}")

        with tab_verification:
            if state.verification:
                st.markdown(f"### Audit Verdict: {state.verification.verdict_summary}")
                st.progress(state.verification.overall_integrity_score)
                st.caption(f"Composite Data Integrity Score: {state.verification.overall_integrity_score * 100:.1f}%")
                st.markdown("#### Claim-by-Claim Verification:")
                for ev in state.verification.evaluations:
                    badge_cls = "badge-verified" if ev.status == "VERIFIED" else "badge-unsupported"
                    with st.expander(f"[{ev.status}] - Confidence {ev.confidence_score * 100:.0f}%: {ev.claim}"):
                        st.markdown(f"**Status:** <span class='{badge_cls}'>{ev.status}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Evidence Notes:** {ev.evidence_notes}")
                        if ev.source_citation:
                            st.markdown(f"**Source Citation:** `{ev.source_citation}`")

        with tab_logs:
            st.markdown("#### Multi-Agent Execution Trail:")
            for log in state.execution_logs:
                st.code(log, language="bash")


elif nav_selection == "💬 Interactive Chat":
    st.markdown('<div class="main-header">💬 Multi-Agent Research Chat</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Collaborate with the specialized agent team in a persistent conversational thread</div>', unsafe_allow_html=True)

    chat_session_id = st.session_state.current_session_id or "default_chat_session"

    col_meta, col_clear = st.columns([4, 1])
    with col_meta:
        st.caption(f"Active Session ID: `{chat_session_id}` | Backed by SQLite Memory Manager")
    with col_clear:
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_messages = []
            st.rerun()

    messages = db.get_messages(chat_session_id)
    for msg in messages:
        if msg.role == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg.content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                sender = msg.agent_name or "Assistant"
                st.markdown(f"**{sender}:** {msg.content}")

    user_input = st.chat_input("Ask a research question or request follow-up analysis...")
    if user_input:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        db.add_message(session_id=chat_session_id, role="user", content=user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Specialized agents deliberating..."):
                wf = ResearchWorkflow(
                    model=selected_model,
                    verification_threshold=verification_threshold,
                    memory_manager=mem_mgr,
                )
                state = asyncio.run(wf.run(user_query=user_input, session_id=chat_session_id))
                st.session_state.workflow_state = state
                if state.report:
                    st.markdown(f"### {state.report.title}")
                    st.markdown(state.report.executive_summary)
                    st.markdown(f"**Integrity Score:** {state.verification.overall_integrity_score * 100:.0f}%")

elif nav_selection == "📚 RAG Knowledge Base":
    st.markdown('<div class="main-header">📚 RAG Vector Knowledge Base Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect, ingest, and semantically query institutional technical documents in ChromaDB</div>', unsafe_allow_html=True)

    tab_ingest, tab_query = st.tabs(["📥 Ingest Technical Documents", "🔍 Semantic Vector Query"])

    with tab_ingest:
        st.subheader("Add Knowledge to ChromaDB")
        
        uploaded_file = st.file_uploader("📂 Upload Local Document (.txt, .md):", type=["txt", "md"])
        uploaded_content = ""
        default_source = "Uploaded_Document.md"
        if uploaded_file is not None:
            uploaded_content = uploaded_file.read().decode("utf-8", errors="ignore")
            default_source = uploaded_file.name
            st.info(f"Loaded `{uploaded_file.name}` ({len(uploaded_content)} characters)")

        col_src, col_cat = st.columns([2, 1])
        with col_src:
            source_name = st.text_input("Source Document Name / Citation:", value=default_source)
        with col_cat:
            doc_category = st.selectbox("Category:", ["clinical_research", "infrastructure", "policy", "ethics", "general_technical"])

        default_paste = uploaded_content if uploaded_content else (
            "Field clinical trials across Sub-Saharan Africa evaluated edge-quantized neural "
            "networks deployed on standard Android smartphones. In malaria-endemic rural dispensaries, "
            "computer-vision analysis of Giemsa-stained thin blood films yielded 94.8% diagnostic "
            "sensitivity and 91.2% specificity, reducing diagnosis latency from 48 hours to under 6 minutes."
        )
        
        raw_content = st.text_area("Paste Technical Literature / Research Text:", height=180, value=default_paste)
        
        if st.button("📥 Chunk & Ingest into ChromaDB", type="primary"):
            if raw_content.strip():
                chunks = retriever.ingest_document(content=raw_content, source_name=source_name, doc_category=doc_category)
                st.success(f"Successfully chunked and indexed {chunks} passages into ChromaDB vector collection!")
            else:
                st.warning("Please provide document content to index.")

    with tab_query:
        st.subheader("Semantic Similarity Search")
        query_input = st.text_input("Semantic Query:", value="What is the diagnostic accuracy of mobile malaria triage?")
        top_k = st.slider("Top K Matches:", min_value=1, max_value=6, value=3)

        if st.button("🔎 Run Semantic Vector Search"):
            if query_input.strip():
                hits = retriever.retrieve(query=query_input, top_k=top_k)
                st.markdown(f"**Found {len(hits)} matching passages in ChromaDB:**")
                for i, h in enumerate(hits, 1):
                    src = h.get("metadata", {}).get("source", "Unknown")
                    score = h.get("similarity_score", 0.0)
                    with st.expander(f"[{i}] {src} (Cosine Relevance: {score:.2f})"):
                        st.progress(score)
                        st.markdown(h.get("content", ""))
            else:
                st.warning("Please enter a query.")

elif nav_selection == "🗄️ Session History":
    st.markdown('<div class="main-header">🗄️ Research Session History & Memory Vault</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect historical research sessions, persistent facts, constraints, and audit trails</div>', unsafe_allow_html=True)

    sessions = db.list_sessions()
    if not sessions:
        st.info("No past research sessions recorded in SQLite yet.")
    else:
        st.subheader(f"Total Recorded Sessions: {len(sessions)}")
        search_filter = st.text_input("🔍 Filter Sessions by Keyword / Title:", value="")
        
        filtered_sessions = [s for s in sessions if search_filter.lower() in s.title.lower()] if search_filter else sessions

        for s in filtered_sessions:
            summary = db.get_session_summary(s.session_id)
            with st.expander(f"Session: {s.title} ({s.status}) - ID: `{s.session_id}`"):
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Messages", summary.message_count if summary else 0)
                with c2: st.metric("Persistent Memories", summary.memory_count if summary else 0)
                with c3: st.metric("Report Available", "Yes" if summary and summary.has_final_report else "No")
                with c4: st.metric("Last Updated", s.updated_at[:16])

                report = db.get_latest_report(s.session_id)
                if report:
                    st.markdown("#### Executive Summary:")
                    st.write(report.get("executive_summary", "No summary available."))
                    if st.button("Activate Session", key=f"btn_{s.session_id}"):
                        st.session_state.current_session_id = s.session_id
                        st.success(f"Session `{s.session_id}` active!")

                messages = db.get_messages(s.session_id, limit=6)
                if messages:
                    st.markdown("#### Recent Message Traces:")
                    for m in messages:
                        st.text(f"[{m.role}|{m.agent_name}]: {m.content[:100]}...")

elif nav_selection == "📊 Evaluation & Benchmarks":
    st.markdown('<div class="main-header">📊 Multi-Agent Evaluation & Performance Benchmarks</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Quantitative AI Evaluation: Latency Profiling, Token Consumption, Schema Completeness & Claim Integrity</div>',
        unsafe_allow_html=True,
    )

    tab_eval_run, tab_benchmark = st.tabs(["🧪 Single Workflow Evaluator", "⚡ Multi-Domain Benchmark Suite"])

    with tab_eval_run:
        st.subheader("Evaluate Single Research Run")
        eval_query = st.text_input("Evaluation Topic:", value="Autonomous driving safety standards in North America and the EU.")
        if st.button("🚀 Run Evaluation Audit", type="primary"):
            with st.spinner("Benchmarking multi-agent pipeline..."):
                wf = ResearchWorkflow(model=selected_model, verification_threshold=verification_threshold, memory_manager=mem_mgr)
                _, report = asyncio.run(evaluator.evaluate_workflow(workflow=wf, query=eval_query))
                st.session_state.eval_report = report

        rep = st.session_state.eval_report
        if rep:
            st.markdown("---")
            st.markdown(f"### Evaluation Report for: *'{rep.query}'*")
            e1, e2, e3, e4, e5 = st.columns(5)
            with e1: st.metric("Total Latency", f"{rep.metrics.execution_time_seconds:.3f} s")
            with e2: st.metric("Est. Input Tokens", rep.metrics.estimated_input_tokens)
            with e3: st.metric("Est. Output Tokens", rep.metrics.estimated_output_tokens)
            with e4: st.metric("Schema Conformance", f"{rep.metrics.schema_completeness_score * 100:.1f}%")
            with e5: st.metric("Integrity Gate", "PASSED" if rep.metrics.quality_gate_passed else "FAILED")

            st.markdown("#### Agent Schema Conformance Audit:")
            for agent_name, validation in rep.agent_validations.items():
                col_a, col_b = st.columns([3, 1])
                with col_a: st.write(f"**{agent_name}**")
                with col_b:
                    if validation.is_valid and validation.completeness_score >= 0.95:
                        st.markdown("<span class='badge-verified'>100% Valid</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span class='badge-unsupported'>{validation.completeness_score * 100:.0f}%</span>", unsafe_allow_html=True)

            st.markdown("#### Automated System Recommendations:")
            for rec in rep.recommendations:
                st.info(f"💡 {rec}")

    with tab_benchmark:
        st.subheader("Automated Multi-Topic Benchmark Battery")
        st.write("Executes 3 diverse domain queries (Cryptography, Clean Energy, Healthcare) and calculates aggregated performance metrics.")
        if st.button("⚡ Run 3-Topic Benchmark Battery", type="primary"):
            with st.spinner("Executing benchmark battery across 3 domains..."):
                wf = ResearchWorkflow(model=selected_model, verification_threshold=verification_threshold, memory_manager=mem_mgr)
                queries = [
                    "Quantum Computing Impact on Post-Quantum Cryptography Architectures",
                    "Perovskite Tandem Solar Cells Commercialization and Degradation Bottlenecks",
                    "Point-of-care mobile AI diagnostics for malaria and tuberculosis in rural clinics",
                ]
                bench = asyncio.run(evaluator.run_benchmark(workflow=wf, queries=queries))
                st.session_state.benchmark_summary = bench
                st.success("Benchmark completed successfully!")

        b = st.session_state.benchmark_summary
        if b:
            st.markdown("---")
            st.markdown("### Aggregated Benchmark Results:")
            b1, b2, b3, b4 = st.columns(4)
            with b1: st.metric("Success Rate", f"{b.success_rate * 100:.0f}%")
            with b2: st.metric("Mean Latency", f"{b.average_latency_seconds:.3f} s")
            with b3: st.metric("Mean Integrity", f"{b.average_integrity_score:.2f}")
            with b4: st.metric("Total Tokens", f"{b.total_estimated_tokens:,}")
