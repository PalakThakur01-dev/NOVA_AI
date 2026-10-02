import streamlit as st
from model import llm
from datetime import datetime
import sqlite3


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="NOVA AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "nova_ai.db"


def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


def create_database():

    conn = get_connection()
    cursor = conn.cursor()

    # Conversations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            created_at TEXT NOT NULL

        )
    """)

    # Messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            conversation_id INTEGER NOT NULL,

            role TEXT NOT NULL,

            content TEXT NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY (conversation_id)
            REFERENCES conversations(id)

        )
    """)

    # Check whether pinned column exists
    cursor.execute("""
        PRAGMA table_info(conversations)
    """)

    columns = [
        column["name"]
        for column in cursor.fetchall()
    ]

    if "pinned" not in columns:

        cursor.execute("""
            ALTER TABLE conversations
            ADD COLUMN pinned INTEGER DEFAULT 0
        """)

    conn.commit()

    conn.close()


create_database()


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def create_conversation(title):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO conversations
        (title, created_at, pinned)

        VALUES (?, ?, ?)
    """, (
        title,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        0
    ))

    conversation_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return conversation_id


def save_message(
    conversation_id,
    role,
    content
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO messages
        (
            conversation_id,
            role,
            content,
            created_at
        )

        VALUES (?, ?, ?, ?)
    """, (
        conversation_id,
        role,
        content,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

    conn.close()


def get_messages(conversation_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content

        FROM messages

        WHERE conversation_id = ?

        ORDER BY id ASC
    """, (conversation_id,))

    rows = cursor.fetchall()

    conn.close()

    messages = []

    for row in rows:

        messages.append({

            "role": row["role"],

            "content": row["content"]

        })

    return messages


def get_conversations(search=""):

    conn = get_connection()
    cursor = conn.cursor()

    if search.strip():

        cursor.execute("""
            SELECT *

            FROM conversations

            WHERE title LIKE ?

            ORDER BY pinned DESC, id DESC
        """, (
            f"%{search.strip()}%",
        ))

    else:

        cursor.execute("""
            SELECT *

            FROM conversations

            ORDER BY pinned DESC, id DESC
        """)

    conversations = cursor.fetchall()

    conn.close()

    return conversations


def delete_conversation(conversation_id):

    conn = get_connection()
    cursor = conn.cursor()

    # Delete messages first
    cursor.execute("""
        DELETE FROM messages

        WHERE conversation_id = ?
    """, (conversation_id,))

    # Delete conversation
    cursor.execute("""
        DELETE FROM conversations

        WHERE id = ?
    """, (conversation_id,))

    conn.commit()

    conn.close()


def rename_conversation(
    conversation_id,
    new_title
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE conversations

        SET title = ?

        WHERE id = ?
    """, (
        new_title,
        conversation_id
    ))

    conn.commit()

    conn.close()


def toggle_pin(conversation_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pinned

        FROM conversations

        WHERE id = ?
    """, (conversation_id,))

    row = cursor.fetchone()

    if row:

        new_value = 0 if row["pinned"] else 1

        cursor.execute("""
            UPDATE conversations

            SET pinned = ?

            WHERE id = ?
        """, (
            new_value,
            conversation_id
        ))

    conn.commit()

    conn.close()


# =========================================================
# SESSION STATE
# =========================================================

if "theme" not in st.session_state:

    st.session_state.theme = "Light"


if "active_page" not in st.session_state:

    st.session_state.active_page = "Home"


if "messages" not in st.session_state:

    st.session_state.messages = []


if "current_chat_id" not in st.session_state:

    st.session_state.current_chat_id = None


if "search_text" not in st.session_state:

    st.session_state.search_text = ""


# =========================================================
# THEME
# =========================================================

if st.session_state.theme == "Light":

    BG = """
    radial-gradient(
        circle at 50% -20%,
        #eef2ff 0%,
        #f8fafc 45%,
        #ffffff 80%
    )
    """

    SIDEBAR = "#ffffff"

    TEXT = "#111827"

    SECONDARY = "#64748b"

    CARD = "rgba(255,255,255,0.90)"

    BORDER = "rgba(15,23,42,0.10)"

    INPUT = "#ffffff"

    SIDEBAR_HOVER = "rgba(99,102,241,0.08)"

else:

    BG = """
    radial-gradient(
        circle at 50% -20%,
        #263653 0%,
        #111827 35%,
        #080b12 75%
    )
    """

    SIDEBAR = "#080b12"

    TEXT = "#f8fafc"

    SECONDARY = "#94a3b8"

    CARD = "rgba(255,255,255,0.035)"

    BORDER = "rgba(255,255,255,0.08)"

    INPUT = "rgba(15,23,42,0.95)"

    SIDEBAR_HOVER = "rgba(99,102,241,0.10)"


# =========================================================
# CSS
# =========================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    .block-container {{
        max-width: 1180px;
        padding-top: 0.5rem;
        padding-bottom: 120px;
    }}

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    header {{
        background: transparent !important;
    }}

    /* SIDEBAR */

    section[data-testid="stSidebar"] {{
        background: {SIDEBAR};
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] > div {{
        padding: 25px 18px;
    }}

    .brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 25px;
    }}

    .brand-logo {{
        width: 44px;
        height: 44px;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 13px;

        background: linear-gradient(
            135deg,
            #7c3aed,
            #2563eb
        );

        color: white;
        font-size: 22px;

        box-shadow:
            0 8px 25px rgba(99,102,241,0.35);
    }}

    .brand-text h2 {{
        margin: 0;
        color: {TEXT};
        font-size: 18px;
    }}

    .brand-text span {{
        color: {SECONDARY};
        font-size: 11px;
    }}

    section[data-testid="stSidebar"]
    .stButton > button {{
        background: transparent;

        border: 1px solid transparent;

        color: {SECONDARY};

        border-radius: 10px;

        text-align: left;

        font-size: 13px;

        transition: 0.2s;
    }}

    section[data-testid="stSidebar"]
    .stButton > button:hover {{
        background: {SIDEBAR_HOVER};

        color: {TEXT};

        border-color:
            rgba(99,102,241,0.20);
    }}

    .side-title {{
        color: {SECONDARY};

        font-size: 10px;

        font-weight: 700;

        text-transform: uppercase;

        letter-spacing: 1.2px;

        margin: 22px 5px 10px 5px;
    }}

    .history-empty {{
        color: {SECONDARY};

        font-size: 12px;

        padding: 10px 5px;

        line-height: 1.5;
    }}

    /* TOPBAR */

    .topbar {{
        height: 62px;

        display: flex;

        align-items: center;

        justify-content: space-between;

        border-bottom:
            1px solid {BORDER};

        margin-bottom: 10px;
    }}

    .model-name {{
        display: flex;

        align-items: center;

        gap: 9px;

        color: {TEXT};

        font-size: 14px;

        font-weight: 600;
    }}

    .online-dot {{
        width: 8px;

        height: 8px;

        border-radius: 50%;

        background: #22c55e;

        box-shadow:
            0 0 10px rgba(34,197,94,0.7);
    }}

    .status {{
        color: {SECONDARY};

        font-size: 12px;
    }}

    /* HERO */

    .hero {{
        text-align: center;

        padding-top: 70px;

        padding-bottom: 35px;
    }}

    .hero-icon {{
        width: 74px;

        height: 74px;

        margin: auto;

        display: flex;

        align-items: center;

        justify-content: center;

        border-radius: 22px;

        background: linear-gradient(
            135deg,
            #6366f1,
            #8b5cf6,
            #2563eb
        );

        color: white;

        font-size: 32px;

        box-shadow:
            0 15px 45px rgba(99,102,241,0.28);
    }}

    .hero h1 {{
        margin-top: 24px;

        margin-bottom: 10px;

        color: {TEXT};

        font-size: 38px;

        font-weight: 700;
    }}

    .hero p {{
        max-width: 600px;

        margin: auto;

        color: {SECONDARY};

        font-size: 15px;

        line-height: 1.6;
    }}

    /* PROMPT CARDS */

    .prompt-card {{
        height: 135px;

        padding: 18px;

        border-radius: 16px;

        background: {CARD};

        border:
            1px solid {BORDER};

        backdrop-filter: blur(12px);
    }}

    .prompt-icon {{
        font-size: 23px;

        margin-bottom: 10px;
    }}

    .prompt-card h4 {{
        margin: 0;

        color: {TEXT};

        font-size: 15px;
    }}

    .prompt-card p {{
        margin-top: 7px;

        color: {SECONDARY};

        font-size: 12px;

        line-height: 1.5;
    }}

    /* CHAT INPUT */

    div[data-testid="stChatInput"] {{
        max-width: 850px;

        margin: auto;
    }}

    div[data-testid="stChatInput"] > div {{
        background: {INPUT} !important;

        border:
            1px solid {BORDER} !important;

        border-radius: 17px !important;

        box-shadow:
            0 10px 40px rgba(0,0,0,0.18) !important;
    }}

    div[data-testid="stChatInput"] textarea {{
        color: {TEXT} !important;

        font-size: 14px !important;
    }}

    /* PANEL */

    .panel {{
        background: {CARD};

        border:
            1px solid {BORDER};

        border-radius: 18px;

        padding: 30px;

        margin: 40px auto;

        max-width: 850px;
    }}

    .panel h2 {{
        color: {TEXT};
    }}

    .panel p {{
        color: {SECONDARY};

        line-height: 1.6;
    }}

    .setting-box {{
        padding: 18px;

        border-radius: 14px;

        background:
            rgba(99,102,241,0.06);

        border:
            1px solid rgba(99,102,241,0.15);

        margin-top: 20px;
    }}

    .footer {{
        text-align: center;

        margin-top: 35px;

        color: {SECONDARY};

        font-size: 11px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    # =====================================================
    # BRAND
    # =====================================================

    st.html("""
    <div class="brand">

        <div class="brand-logo">
            ✦
        </div>

        <div class="brand-text">

            <h2>NOVA AI</h2>

            <span>
                Intelligent Assistant
            </span>

        </div>

    </div>
    """)


    # =====================================================
    # NEW CONVERSATION
    # =====================================================

    if st.button(
        "＋  New Conversation",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.current_chat_id = None

        st.session_state.active_page = "Home"

        st.rerun()


    # =====================================================
    # SEARCH
    # =====================================================

    st.html("""
    <div class="side-title">
        Search Conversations
    </div>
    """)


    search_text = st.text_input(
        "Search",
        placeholder="Search chats...",
        label_visibility="collapsed"
    )


    # =====================================================
    # RECENT CONVERSATIONS
    # =====================================================

    st.html("""
    <div class="side-title">
        Recent Conversations
    </div>
    """)


    conversations = get_conversations(
        search_text
    )


    if not conversations:

        st.html("""
        <div class="history-empty">
            No conversations found.
        </div>
        """)

    else:

        for chat in conversations:

            conversation_id = chat["id"]

            title = chat["title"]

            display_title = title

            if len(display_title) > 25:

                display_title = (
                    display_title[:25] + "..."
                )


            # ---------------------------------------------
            # CHAT ROW
            # ---------------------------------------------

            col1, col2, col3 = st.columns(
                [6, 1, 1]
            )


            # ---------------------------------------------
            # OPEN CHAT
            # ---------------------------------------------

            with col1:

                pin_icon = (
                    "📌 "
                    if chat["pinned"]
                    else ""
                )

                if st.button(
                    f"{pin_icon}💬 {display_title}",
                    key=f"open_{conversation_id}",
                    use_container_width=True
                ):

                    st.session_state.messages = (
                        get_messages(
                            conversation_id
                        )
                    )

                    st.session_state.current_chat_id = (
                        conversation_id
                    )

                    st.session_state.active_page = (
                        "Home"
                    )

                    st.rerun()


            # ---------------------------------------------
            # PIN
            # ---------------------------------------------

            with col2:

                pin_button = (
                    "📌"
                    if chat["pinned"]
                    else "📍"
                )

                if st.button(
                    pin_button,
                    key=f"pin_{conversation_id}"
                ):

                    toggle_pin(
                        conversation_id
                    )

                    st.rerun()


            # ---------------------------------------------
            # DELETE
            # ---------------------------------------------

            with col3:

                if st.button(
                    "🗑️",
                    key=f"delete_{conversation_id}"
                ):

                    delete_conversation(
                        conversation_id
                    )


                    # If deleting current chat
                    if (
                        st.session_state.current_chat_id
                        == conversation_id
                    ):

                        st.session_state.messages = []

                        st.session_state.current_chat_id = (
                            None
                        )


                    st.rerun()


            # Date & time
            st.caption(
                f"📅 {chat['created_at']}"
            )


    # =====================================================
    # RENAME CURRENT CHAT
    # =====================================================

    if st.session_state.current_chat_id:

        with st.expander("✏️ Rename Conversation"):

            current_chat_id = (
                st.session_state.current_chat_id
            )


            current_conversations = (
                get_conversations()
            )


            current_title = "Conversation"


            for chat in current_conversations:

                if chat["id"] == current_chat_id:

                    current_title = chat["title"]

                    break


            new_title = st.text_input(
                "New title",
                value=current_title,
                key="rename_input"
            )


            if st.button(
                "Save New Name",
                use_container_width=True
            ):

                new_title = new_title.strip()


                if new_title:

                    rename_conversation(
                        current_chat_id,
                        new_title
                    )

                    st.success(
                        "Conversation renamed!"
                    )

                    st.rerun()


    # =====================================================
    # WORKSPACE
    # =====================================================

    st.html("""
    <div class="side-title">
        Workspace
    </div>
    """)


    # Settings
    if st.button(
        "⚙️  Settings",
        use_container_width=True
    ):

        st.session_state.active_page = "Settings"

        st.rerun()


    # Help
    if st.button(
        "❓  Help & Support",
        use_container_width=True
    ):

        st.session_state.active_page = "Help"

        st.rerun()


    st.divider()

    st.caption(
        "NOVA AI • Version 1.0"
    )


# =========================================================
# SETTINGS PAGE
# =========================================================

if st.session_state.active_page == "Settings":

    st.html("""
    <div class="topbar">

        <div class="model-name">
            ⚙️ Settings
        </div>

        <div class="status">
            Customize your experience
        </div>

    </div>
    """)


    st.html("""
    <div class="panel">

        <h2>⚙️ Settings</h2>

        <p>
            Customize the appearance of your
            NOVA AI interface.
        </p>

    </div>
    """)


    st.subheader("🎨 Appearance")


    theme = st.radio(
        "Choose Theme",

        ["Light", "Dark"],

        index=
            0
            if st.session_state.theme == "Light"
            else 1,

        horizontal=True
    )


    if theme != st.session_state.theme:

        st.session_state.theme = theme

        st.rerun()


    st.html(f"""
    <div class="setting-box">

        <strong style="color:{TEXT};">
            Current Theme
        </strong>

        <p
            style="
                color:{SECONDARY};
                margin-bottom:0;
            "
        >
            {st.session_state.theme}
            mode is currently active.
        </p>

    </div>
    """)


    st.divider()


    if st.button("← Back to Chat"):

        st.session_state.active_page = "Home"

        st.rerun()


# =========================================================
# HELP PAGE
# =========================================================

elif st.session_state.active_page == "Help":

    st.html("""
    <div class="topbar">

        <div class="model-name">
            ❓ Help & Support
        </div>

        <div class="status">
            Need assistance?
        </div>

    </div>
    """)


    st.html("""
    <div class="panel">

        <h2>❓ Help & Support</h2>

        <p>
            Welcome to NOVA AI.
            Here are some quick details
            about using the application.
        </p>


        <div class="setting-box">

            <strong>
                💬 Start a conversation
            </strong>

            <p>
                Type your question in the
                message box at the bottom.
            </p>

        </div>


        <div class="setting-box">

            <strong>
                🔍 Search Conversations
            </strong>

            <p>
                Search your old conversations
                from the sidebar.
            </p>

        </div>


        <div class="setting-box">

            <strong>
                📌 Pin Conversations
            </strong>

            <p>
                Pin important conversations
                so they stay at the top.
            </p>

        </div>


        <div class="setting-box">

            <strong>
                ✏️ Rename Conversation
            </strong>

            <p>
                Open a conversation and use
                Rename Conversation from the sidebar.
            </p>

        </div>


        <div class="setting-box">

            <strong>
                🗑️ Delete Conversation
            </strong>

            <p>
                Click the trash icon beside a
                conversation to delete it.
            </p>

        </div>

    </div>
    """)


    if st.button("← Back to Chat"):

        st.session_state.active_page = "Home"

        st.rerun()


# =========================================================
# HOME PAGE
# =========================================================

else:

    # =====================================================
    # TOP BAR
    # =====================================================

    st.html("""
    <div class="topbar">

        <div class="model-name">

            <div class="online-dot"></div>

            NOVA AI

        </div>

        <div class="status">
            AI Assistant
        </div>

    </div>
    """)


    # =====================================================
    # EMPTY CHAT
    # =====================================================

    if not st.session_state.messages:

        st.html("""
        <div class="hero">

            <div class="hero-icon">
                ✦
            </div>

            <h1>
                What can I help you with?
            </h1>

            <p>
                Ask questions, explore ideas,
                write code, learn concepts,
                or solve problems with NOVA AI.
            </p>

        </div>
        """)


        # Prompt cards

        col1, col2, col3, col4 = st.columns(4)


        with col1:

            st.html("""
            <div class="prompt-card">

                <div class="prompt-icon">
                    💡
                </div>

                <h4>
                    Learn
                </h4>

                <p>
                    Understand difficult concepts
                    with simple explanations.
                </p>

            </div>
            """)


        with col2:

            st.html("""
            <div class="prompt-card">

                <div class="prompt-icon">
                    💻
                </div>

                <h4>
                    Code
                </h4>

                <p>
                    Write, understand and debug
                    your programming code.
                </p>

            </div>
            """)


        with col3:

            st.html("""
            <div class="prompt-card">

                <div class="prompt-icon">
                    🚀
                </div>

                <h4>
                    Projects
                </h4>

                <p>
                    Build real-world projects
                    step by step.
                </p>

            </div>
            """)


        with col4:

            st.html("""
            <div class="prompt-card">

                <div class="prompt-icon">
                    ✨
                </div>

                <h4>
                    Ideas
                </h4>

                <p>
                    Brainstorm ideas and discover
                    new possibilities.
                </p>

            </div>
            """)


    # =====================================================
    # SHOW CURRENT CHAT
    # =====================================================

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    # =====================================================
    # CHAT INPUT
    # =====================================================

    if prompt := st.chat_input(
        "Message NOVA AI..."
    ):


        # =================================================
        # CREATE NEW CONVERSATION
        # =================================================

        if st.session_state.current_chat_id is None:

            chat_title = prompt.strip()


            if len(chat_title) > 32:

                chat_title = (
                    chat_title[:32] + "..."
                )


            conversation_id = (
                create_conversation(
                    chat_title
                )
            )


            st.session_state.current_chat_id = (
                conversation_id
            )


        # =================================================
        # USER MESSAGE
        # =================================================

        st.session_state.messages.append({

            "role": "user",

            "content": prompt

        })


        save_message(

            st.session_state.current_chat_id,

            "user",

            prompt

        )


        with st.chat_message("user"):

            st.markdown(prompt)


        # =================================================
        # AI RESPONSE
        # =================================================

        with st.chat_message("assistant"):

            response_placeholder = st.empty()

            full_response = ""


            for token in llm.stream(
                st.session_state.messages
            ):

                token_text = (
                    token.content or ""
                )


                full_response += token_text


                response_placeholder.markdown(
                    full_response + "▌"
                )


            response_placeholder.markdown(
                full_response
            )


        # =================================================
        # SAVE AI RESPONSE
        # =================================================

        st.session_state.messages.append({

            "role": "assistant",

            "content": full_response

        })


        save_message(

            st.session_state.current_chat_id,

            "assistant",

            full_response

        )


        st.rerun()


    # =====================================================
    # FOOTER
    # =====================================================

    st.html("""
    <div class="footer">

        NOVA AI can make mistakes.
        Always verify important information.

    </div>
    """)