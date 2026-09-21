import streamlit as st
import json
import re
from google import genai


# =========================================================
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="StudyAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# GEMINI
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

MODEL = "gemini-3.6-flash"


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "step": 1,
    "name": "",
    "subject": "",
    "notes": "",
    "difficulty": "Easy",
    "quiz": [],
    "question_number": 0,
    "score": 0,
    "wrong_questions": [],
    "answer_checked": False,
    "last_result": None,
    "review": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# GEMINI FUNCTIONS
# =========================================================

def clean_json(text):

    text = text.strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?",
            "",
            text
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

    return text.strip()


# =========================================================
# GENERATE QUESTIONS
# =========================================================

def generate_questions(
    notes,
    subject,
    difficulty
):

    prompt = f"""
You are StudyAI, an AI study assistant.

Subject:
{subject}

Student notes:
{notes}

Difficulty:
{difficulty}

Create exactly 5 multiple-choice questions based ONLY on
the student's notes.

Each question must have:
- one question
- exactly 4 answer choices
- one correct answer

Difficulty rules:

Easy:
Basic definitions and recall.

Medium:
Understanding, explanations and comparisons.

Hard:
Application, reasoning and connecting concepts.

Return ONLY valid JSON.

Use exactly this structure:

[
  {{
    "question": "Question here",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "The exact correct option"
  }}
]

Do not add anything before or after the JSON.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = clean_json(response.text)

    try:

        questions = json.loads(text)

        if not isinstance(questions, list):
            raise ValueError(
                "Questions were not returned as a list."
            )

        if len(questions) != 5:
            raise ValueError(
                "Gemini did not return exactly 5 questions."
            )

        return questions

    except Exception:

        st.error(
            "StudyAI couldn't read the questions Gemini generated."
        )

        st.code(response.text)

        return []


# =========================================================
# CHECK ANSWER
# =========================================================

def check_answer_with_ai(
    question,
    selected_answer,
    correct_answer
):

    prompt = f"""
You are checking a multiple-choice answer.

Question:
{question}

Correct answer:
{correct_answer}

Student selected:
{selected_answer}

Determine whether the student is correct.

Return ONLY valid JSON:

{{
    "correct": true,
    "explanation": "Short simple explanation"
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    text = clean_json(response.text)

    try:

        return json.loads(text)

    except Exception:

        return {
            "correct": selected_answer == correct_answer,
            "explanation": ""
        }


# =========================================================
# GENERATE REVIEW
# =========================================================

def generate_review(
    wrong_questions,
    subject
):

    if not wrong_questions:

        return (
            "Amazing work! You answered every question correctly. "
            "Keep reviewing your notes to make sure you remember everything."
        )

    wrong_text = ""

    for item in wrong_questions:

        wrong_text += f"""
Question:
{item["question"]}

Correct answer:
{item["answer"]}

Student answer:
{item["student_answer"]}
"""

    prompt = f"""
You are StudyAI.

The student studied:
{subject}

These are the questions they got wrong:

{wrong_text}

Create a short study review.

For each mistake:
- Explain the idea simply.
- Give a useful memory tip.
- Give a short example if helpful.

Keep it simple and student-friendly.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text


# =========================================================
# DESIGN
# =========================================================

st.markdown(
"""
<style>

@import url(
    'https://fonts.googleapis.com/css2?family=Luckiest+Guy&display=swap'
);


/* =======================================================
GLOBAL PAGE
======================================================= */

.stApp {
    background: #dcb9d9;
}

.main .block-container {
    max-width: 1450px;
    padding-top: 10px;
    padding-bottom: 50px;
}


/* =======================================================
GLOBAL TEXT
======================================================= */

.stApp,
.stApp p,
.stApp label,
.stApp span,
.stApp div {
    color: #1c1017;
}


/* =======================================================
STUDYAI LOGO
======================================================= */

.study-title {

    font-family:
        "Luckiest Guy",
        "Arial Black",
        Impact,
        sans-serif;

    font-size: 100px;

    font-weight: 400;

    color: #4b001f !important;

    letter-spacing: 2px;

    line-height: 0.82;

    -webkit-text-stroke:
        2px #160b10;

    text-shadow:
        3px 3px 0 #160b10,
        6px 6px 0 rgba(0,0,0,0.14);

    transform: rotate(-1deg);

    margin-bottom: 5px;
}


/* =======================================================
SUBTITLE
======================================================= */

.study-subtitle {

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif;

    font-size: 25px;

    font-weight: 800;

    color: #1d1017 !important;

    text-shadow:
        0.7px 0.7px 0 #000;

    margin-top: 12px;

    margin-bottom: 5px;
}


/* =======================================================
AI BADGE
======================================================= */

.ai-badge {

    display: inline-block;

    background: #f4d45c;

    color: #1a1012 !important;

    font-family:
        "Comic Sans MS",
        sans-serif;

    font-size: 17px;

    font-weight: 900;

    padding: 9px 18px;

    border-radius:
        25px 18px 27px 20px;

    border:
        2px solid #171014;

    transform: rotate(-2deg);

    box-shadow:
        3px 4px 0 #76516c;

    margin-top: 15px;

    margin-bottom: 25px;
}


/* =======================================================
LEFT SIDE
======================================================= */

.question-title {

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif;

    font-size: 48px;

    font-weight: 900;

    line-height: 1;

    color: #4d1028 !important;

    -webkit-text-stroke:
        1px #12090d;

    text-shadow:
        2px 2px 0 #12090d;

    transform: rotate(-1deg);

    margin-top: 60px;
}


.question-help {

    font-family:
        "Comic Sans MS",
        sans-serif;

    font-size: 18px;

    font-weight: 700;

    color: #21131a !important;

    max-width: 470px;

    margin-top: 18px;

    line-height: 1.5;

    text-shadow:
        0.5px 0.5px 0 #000;
}


/* =======================================================
   HAPPY MASCOT (Intro Entrance, Bubble Blow & Instant Pop)
   ======================================================= */

.mascot {
    width: 180px;
    height: 190px;
    background: #8fc4a4;
    border: 5px solid #172d25;
    /* Soft, friendly potato shape */
    border-radius: 55% 45% 52% 48% / 60% 55% 45% 50%;
    margin-top: 42px;
    position: relative;
    box-shadow: 7px 8px 0 rgba(40,20,35,0.20);
    box-sizing: border-box;
    cursor: pointer;
    
    /* Playful Entrance drops in first, then hands off to the idle wobble loop */
    animation: entranceDrop 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards,
               happyWobble 0.8s steps(2) infinite 0.8s;
    
    /* Smooth spring transitions */
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), 
                border-radius 0.3s ease;
}

/* HOVER: Stretches upward slightly while blowing gum */
.mascot:hover {
    animation-play-state: paused;
    transform: scale(1.05) translateY(-5px);
    border-radius: 50% 50% 52% 48% / 55% 55% 45% 45%;
}

/* CLICK / ACTIVE: Squeezes down playfully */
.mascot:active {
    transform: scaleX(1.1) scaleY(0.9) translateY(5px);
    border-radius: 60% 40% 55% 45% / 50% 50% 50% 50%;
    box-shadow: 3px 4px 0 rgba(40,20,35,0.20);
    transition: transform 0.05s ease; /* Instant drop snap */
}


/* EFFORTLESS FLAT DOT EYES */
.eye {
    width: 14px;
    height: 14px;
    background: #172d25;
    border-radius: 50%;
    position: absolute;
    top: 72px;
    z-index: 2;
    box-sizing: border-box;
    
    /* Clean, happy blinking (starts after drop animation) */
    animation: happyBlink 4s steps(1) infinite 0.8s;
    transition: width 0.1s ease, height 0.1s ease, top 0.1s ease, background 0.1s ease, border 0.1s ease;
}

.eye.left { left: 56px; }
.eye.right { right: 52px; }

/* HOVER EYES: Close into happy crescent squint arcs */
.mascot:hover .eye {
    animation: none;
    width: 16px;
    height: 6px;
    background: transparent;
    border-bottom: 4px solid #172d25;
    border-radius: 0 0 50% 50%;
    top: 76px;
}

/* CLICK / ACTIVE EYES: Widen instantly into huge, wide-staring shocked cartoon eyes! */
.mascot:active .eye {
    animation: none;
    width: 28px;
    height: 28px;
    top: 62px;
    background: #ffffff; /* White eyeball canvas */
    border: 4px solid #172d25; /* Defined dark rim */
    border-radius: 50%;
}

/* Add a tiny central pupil inside the wide shocked eyes */
.mascot:active .eye::before {
    content: "";
    position: absolute;
    width: 8px;
    height: 8px;
    background: #172d25;
    border-radius: 50%;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
}


/* FRIENDLY SMILEY MOUTH */
.mouth {
    position: absolute;
    width: 40px;
    height: 20px;
    border-bottom: 5px solid #172d25;
    border-radius: 0 0 40px 40px; 
    left: 68px;
    top: 98px;
    z-index: 2;
    transform-origin: center;
    
    /* Gentle smile balancing animation */
    animation: happyMouth 0.8s steps(2) infinite 0.8s;
    
    transition: transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275),
                width 0.25s ease,
                height 0.25s ease,
                top 0.25s ease,
                left 0.25s ease;
}

/* HOVER MOUTH: Opens wider into an O-shape to blow the bubble */
.mascot:hover .mouth {
    animation-play-state: paused;
    width: 24px;
    height: 24px;
    left: 76px;
    top: 94px;
    border: 5px solid #172d25;
    border-radius: 50%;
}

/* CLICK / ACTIVE MOUTH: Drops slightly lower and flattens out into an 'oops' line */
.mascot:active .mouth {
    animation: none;
    width: 32px;
    height: 10px;
    left: 72px;
    top: 104px;
    border-radius: 0 0 20px 20px;
}


/* PINK BUBBLE GUM & SPLATTER */
.mouth::after {
    content: "";
    position: absolute;
    background: #ffb1cb;
    border: 4px solid #172d25;
    border-radius: 50%;
    box-shadow: inset 4px 4px 0 rgba(255, 255, 255, 0.6);
    
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%) scale(0);
    z-index: 3;
    
    /* Smooth growth transition */
    transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.5);
    transform-origin: center;
}

/* HOVER BUBBLE: Inflates out of the mouth */
.mascot:hover .mouth::after {
    width: 50px;
    height: 50px;
    transform: translate(-30%, -40%) scale(1);
}

/* CLICK/ACTIVE POP: Instantly snaps scale down while generating pop splatters via box-shadow */
.mascot:active .mouth::after {
    transform: translate(-50%, -50%) scale(0);
    transition: transform 0.01s ease; /* Ultra instantaneous speed */
}

/* POP SPLATTER PARTICLES (Simulated via a hidden companion tag structure) */
.mascot::after {
    content: "";
    position: absolute;
    width: 6px;
    height: 6px;
    background: #ffb1cb;
    border-radius: 50%;
    left: 90px;
    top: 110px;
    opacity: 0;
    z-index: 4;
}

/* Trigger a burst distribution of particles only during the active click frame */
.mascot:active::after {
    opacity: 1;
    box-shadow: 
        -40px -25px 0 #ffb1cb,  /* Left burst fragment */
         45px -15px 0 #ffb1cb,  /* Right burst fragment */
         5px -55px 0 #ffb1cb,   /* Upward burst fragment */
        -15px 35px 0 #ffb1cb;   /* Downward burst fragment */
    transform: scale(1.5);
    transition: all 0.05s ease-out;
}


/* =======================================================
   HAPPY ANIMATION KEYFRAMES
   ======================================================= */

/* INTRO: Drops down from off-screen, squishes, and settles */
@keyframes entranceDrop {
    0% {
        transform: translateY(-500px) scaleY(1.4);
    }
    60% {
        transform: translateY(15px) scaleY(0.7) scaleX(1.2); /* Squash layout on land */
    }
    80% {
        transform: translateY(-8px) scaleY(1.1) scaleX(0.95); /* Spring bounce back up */
    }
    100% {
        transform: translateY(0) scale(1);
    }
}

/* IDLE: Bouncy, cheerful hand-drawn wobble */
@keyframes happyWobble {
    0% { transform: rotate(-1deg) scaleY(1); }
    50% { transform: rotate(2deg) scaleY(1.02); }
}

/* IDLE: Peaceful, quick blink */
@keyframes happyBlink {
    0%, 92%, 100% { height: 14px; top: 72px; }
    96% { height: 2px; top: 78px; }
}

/* IDLE: Gentle mouth tilt */
@keyframes happyMouth {
    0% { transform: rotate(-1deg); }
    50% { transform: rotate(1deg); }
}

/* =======================================================
NOTEBOOK
======================================================= */

.st-key-notebook {

    background-color: #fffdf2;

    border:
        3px solid #21151b;

    border-radius:
        20px 8px 25px 12px;

    min-height: 500px;

    padding:
        35px
        50px
        40px
        90px;

    margin-top: -10px;

    box-shadow:
        9px 10px 0 rgba(56,25,47,0.30);

    transform: rotate(0.5deg);

    position: relative;

    overflow: hidden;

    background-image:

        linear-gradient(
            90deg,
            transparent 0,
            transparent 63px,
            rgba(221,83,105,0.48) 64px,
            rgba(221,83,105,0.48) 66px,
            transparent 67px
        ),

        repeating-linear-gradient(
            to bottom,
            transparent 0px,
            transparent 39px,
            rgba(75,135,180,0.35) 40px,
            rgba(75,135,180,0.35) 41px,
            transparent 42px
        );
}


/* NOTEBOOK STAR */

.st-key-notebook::before {

    content: "✦";

    position: absolute;

    top: 18px;

    right: 25px;

    font-size: 30px;

    color: #e4bd42;

    -webkit-text-stroke:
        1px #6c5416;

    transform: rotate(12deg);
}


/* =======================================================
NOTEBOOK CONTENT
======================================================= */

.notebook-heading {

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif;

    font-size: 25px;

    font-weight: 900;

    color: #35101e !important;

    -webkit-text-stroke:
        0.6px #12090d;

    text-shadow:
        1px 1px 0 #000;

    margin-bottom: 10px;
}


.notebook-text {

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif;

    font-size: 18px;

    font-weight: 700;

    color: #20141a !important;

    line-height: 1.7;

    text-shadow:
        0.4px 0.4px 0 #000;
}


/* =======================================================
INPUTS
======================================================= */

.st-key-name_input input,
.st-key-subject_input input,
.st-key-notes_input textarea,
.st-key-answer_input textarea {

    background:
        rgba(255,255,255,0.12) !important;

    border: none !important;

    border-bottom:
        3px dashed #21151b !important;

    border-radius: 0 !important;

    box-shadow: none !important;

    color: #160d12 !important;

    -webkit-text-fill-color:
        #160d12 !important;

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif !important;

    font-size: 21px !important;

    font-weight: 700 !important;

    text-shadow:
        0.5px 0.5px 0 #000;
}


.st-key-name_input input:focus,
.st-key-subject_input input:focus,
.st-key-notes_input textarea:focus,
.st-key-answer_input textarea:focus {

    background:
        rgba(255,255,255,0.18) !important;

    border-bottom:
        3px solid #21151b !important;

    box-shadow: none !important;
}


/* =======================================================
PLACEHOLDERS
======================================================= */

.st-key-name_input input::placeholder,
.st-key-subject_input input::placeholder,
.st-key-notes_input textarea::placeholder,
.st-key-answer_input textarea::placeholder {

    color: #4c3942 !important;

    opacity: 1 !important;

    font-weight: 600 !important;
}


.st-key-notes_input textarea {

    min-height: 180px !important;

    line-height: 40px !important;
}


/* =======================================================
DIFFICULTY
======================================================= */

.st-key-difficulty_choice [role="radiogroup"] {

    gap: 14px !important;

    display: flex !important;

    flex-direction: column !important;

    margin-top: 15px !important;
}


.st-key-difficulty_choice label {

    background: #f5e8c7 !important;

    border:
        3px solid #21151b !important;

    border-radius:
        14px 10px 15px 12px !important;

    padding:
        13px 20px !important;

    min-height: 52px !important;

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif !important;

    font-size: 20px !important;

    font-weight: 900 !important;

    color: #171015 !important;

    box-shadow:
        3px 4px 0 rgba(50,25,40,0.22) !important;

    text-shadow:
        0.5px 0.5px 0 #000 !important;
}


/* =======================================================
MULTIPLE CHOICE
======================================================= */

.st-key-answer_choice [role="radiogroup"] {

    display: flex !important;

    flex-direction: column !important;

    gap: 12px !important;

    margin-top: 18px !important;
}


.st-key-answer_choice label {

    background:
        rgba(255,255,255,0.48) !important;

    border:
        3px dashed #21151b !important;

    border-radius:
        13px 10px 15px 11px !important;

    padding:
        13px 18px !important;

    min-height: 48px !important;

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif !important;

    font-size: 19px !important;

    font-weight: 800 !important;

    color: #160d12 !important;

    box-shadow: none !important;

    text-shadow:
        0.6px 0.6px 0 #000 !important;
}


/* =======================================================
QUIZ
======================================================= */

.quiz-number {

    font-family:
        "Comic Sans MS",
        sans-serif;

    font-size: 17px;

    font-weight: 900;

    color: #352027 !important;

    text-shadow:
        0.5px 0.5px 0 #000;

    margin-bottom: 10px;
}


.quiz-question {

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif;

    font-size: 29px;

    font-weight: 900;

    line-height: 1.45;

    color: #3c0d20 !important;

    -webkit-text-stroke:
        0.8px #10080c;

    text-shadow:
        1px 1px 0 #000;

    margin-bottom: 15px;
}


/* =======================================================
BUTTONS
======================================================= */

.stButton > button {

    background: #f4d35e !important;

    color: #160d10 !important;

    border:
        3px solid #21151b !important;

    border-radius:
        10px 17px 8px 15px !important;

    font-family:
        "Comic Sans MS",
        "Trebuchet MS",
        sans-serif !important;

    font-size: 18px !important;

    font-weight: 900 !important;

    padding:
        10px 28px !important;

    box-shadow:
        4px 5px 0 #21151b !important;

    text-shadow:
        0.5px 0.5px 0 #000 !important;

    transform: rotate(-1deg);

    margin-top: 15px;
}


.stButton > button:hover {

    background: #ffe16b !important;

    color: #000 !important;

    transform:
        rotate(1deg)
        translateY(-2px);

    box-shadow:
        5px 7px 0 #21151b !important;
}


/* =======================================================
CORRECT
======================================================= */

.correct-box {

    background: #d8edcf;

    border:
        3px solid #315b35;

    border-radius:
        15px 10px 17px 12px;

    padding:
        15px 20px;

    font-family:
        "Comic Sans MS",
        sans-serif;

    font-size: 18px;

    font-weight: 700;

    color: #172d19 !important;

    margin-top: 20px;

    box-shadow:
        3px 4px 0 rgba(30,50,30,0.18);
}


/* =======================================================
WRONG
======================================================= */

.wrong-box {

    background: #f4cccc;

    border:
        3px solid #64252d;

    border-radius:
        12px 17px 10px 15px;

    padding:
        15px 20px;

    font-family:
        "Comic Sans MS",
        sans-serif;

    font-size: 18px;

    font-weight: 700;

    color: #351015 !important;

    margin-top: 20px;

    box-shadow:
        3px 4px 0 rgba(50,20,25,0.18);
}


/* =======================================================
SCORE
======================================================= */

.score-box {

    font-family:
        "Comic Sans MS",
        sans-serif;

    font-size: 30px;

    font-weight: 900;

    color: #3c0d20 !important;

    -webkit-text-stroke:
        0.8px #10080c;

    text-shadow:
        1px 1px 0 #000;

    text-align: center;

    padding: 20px;
}


/* =======================================================
ALERTS
======================================================= */

[data-testid="stAlert"] {

    border:
        2px solid #21151b !important;

    color:
        #160d12 !important;

    font-family:
        "Comic Sans MS",
        sans-serif !important;

    font-weight:
        700 !important;
}


/* =======================================================
LABELS
======================================================= */

.st-key-name_input label,
.st-key-subject_input label,
.st-key-notes_input label,
.st-key-answer_choice label > div:first-child,
.st-key-difficulty_choice label > div:first-child {

    color:
        #160d12 !important;
}


/* =======================================================
MOBILE
======================================================= */

@media (max-width: 900px) {

    .study-title {
        font-size: 60px;
    }

    .question-title {
        font-size: 38px;
        margin-top: 20px;
    }

    .st-key-notebook {
        padding:
            30px
            25px
            35px
            55px;
    }

    .quiz-question {
        font-size: 24px;
    }

}

</style>
""",
unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="study-title">STUDYAI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="study-subtitle">'
    'Your personal AI study assistant'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="ai-badge">✦ AI POWERED ✦</div>',
    unsafe_allow_html=True
)


# =========================================================
# TWO MAIN SIDES
# =========================================================

left, right = st.columns(
    [0.9, 1.5],
    gap="large"
)


# =========================================================
# LEFT SIDE
# =========================================================

with left:

    if st.session_state.step == 1:

        title = "What's your name?"

        help_text = (
            "Let's get to know you before "
            "we start studying!"
        )

    elif st.session_state.step == 2:

        title = "What are we studying?"

        help_text = (
            "Tell me the subject you want "
            "to practice."
        )

    elif st.session_state.step == 3:

        title = "What are you learning?"

        help_text = (
            "Add your notes and I'll turn "
            "them into a personalized quiz."
        )

    elif st.session_state.step == 4:

        title = "How hard should it be?"

        help_text = (
            "Choose a starting difficulty. "
            "StudyAI can adapt later."
        )

    elif st.session_state.step == 5:

        title = "Let's study!"

        help_text = (
            "Choose the answer you think is correct."
        )

    else:

        title = "Quiz complete!"

        help_text = (
            "Let's see how you did."
        )


    st.markdown(
        f'<div class="question-title">'
        f'{title}'
        f'</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        f'<div class="question-help">'
        f'{help_text}'
        f'</div>',
        unsafe_allow_html=True
    )


    # =====================================================
    # MASCOT
    # =====================================================

    st.html(
        """
        <div class="mascot">

            <div class="eye left"></div>

            <div class="eye right"></div>

            <div class="cheek left"></div>

            <div class="cheek right"></div>

            <div class="mouth"></div>

        </div>
        """
    )


# =========================================================
# RIGHT SIDE
# =========================================================

with right:

    with st.container(key="notebook"):

        # =================================================
        # STEP 1
        # =================================================

        if st.session_state.step == 1:

            st.markdown(
                '<div class="notebook-heading">'
                'Write your name below ✏️'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="notebook-text">'
                'This is your personal StudyAI notebook.'
                '</div>',
                unsafe_allow_html=True
            )

            st.write("")

            name = st.text_input(
                "Name",
                value=st.session_state.name,
                key="name_input",
                label_visibility="collapsed",
                placeholder="Your name..."
            )

            if st.button(
                "CONTINUE →",
                key="btn_step_1"
            ):

                if name.strip():

                    st.session_state.name = name.strip()

                    st.session_state.step = 2

                    st.rerun()

                else:

                    st.warning(
                        "Write your name first."
                    )


        # =================================================
        # STEP 2
        # =================================================

        elif st.session_state.step == 2:

            st.markdown(
                '<div class="notebook-heading">'
                'What subject? 📚'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="notebook-text">'
                'Examples: Biology, Physics, Mathematics...'
                '</div>',
                unsafe_allow_html=True
            )

            st.write("")

            subject = st.text_input(
                "Subject",
                value=st.session_state.subject,
                key="subject_input",
                label_visibility="collapsed",
                placeholder="Your subject..."
            )

            if st.button(
                "CONTINUE →",
                key="btn_step_2"
            ):

                if subject.strip():

                    st.session_state.subject = subject.strip()

                    st.session_state.step = 3

                    st.rerun()

                else:

                    st.warning(
                        "Write a subject first."
                    )


        # =================================================
        # STEP 3
        # =================================================

        elif st.session_state.step == 3:

            st.markdown(
                '<div class="notebook-heading">'
                'Add your notes ✏️'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="notebook-text">'
                'Paste or type the notes you want '
                'StudyAI to use for your quiz.'
                '</div>',
                unsafe_allow_html=True
            )

            notes = st.text_area(
                "Notes",
                value=st.session_state.notes,
                key="notes_input",
                label_visibility="collapsed",
                placeholder="Write your notes here..."
            )

            if st.button(
                "CONTINUE →",
                key="btn_step_3"
            ):

                if notes.strip():

                    st.session_state.notes = notes.strip()

                    st.session_state.step = 4

                    st.rerun()

                else:

                    st.warning(
                        "Write some notes first."
                    )


        # =================================================
        # STEP 4
        # =================================================

        elif st.session_state.step == 4:

            st.markdown(
                '<div class="notebook-heading">'
                'Pick your difficulty ⭐'
                '</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                '<div class="notebook-text">'
                'How challenging do you want '
                'your questions to be?'
                '</div>',
                unsafe_allow_html=True
            )

            difficulty = st.radio(
                "Difficulty",
                [
                    "Easy",
                    "Medium",
                    "Hard"
                ],
                index=[
                    "Easy",
                    "Medium",
                    "Hard"
                ].index(
                    st.session_state.difficulty
                ),
                key="difficulty_choice",
                label_visibility="collapsed"
            )

            if st.button(
                "GENERATE QUIZ ✨",
                key="btn_generate"
            ):

                st.session_state.difficulty = difficulty

                with st.spinner(
                    "StudyAI is creating your quiz..."
                ):

                    questions = generate_questions(
                        st.session_state.notes,
                        st.session_state.subject,
                        difficulty
                    )

                if questions:

                    st.session_state.quiz = questions

                    st.session_state.question_number = 0

                    st.session_state.score = 0

                    st.session_state.wrong_questions = []

                    st.session_state.answer_checked = False

                    st.session_state.last_result = None

                    st.session_state.review = ""

                    st.session_state.step = 5

                    st.rerun()


        # =================================================
        # STEP 5
        # =================================================

        elif st.session_state.step == 5:

            index = st.session_state.question_number

            total = len(st.session_state.quiz)

            if index >= total:

                st.session_state.step = 6

                st.rerun()

            question = st.session_state.quiz[index]

            st.markdown(
                f'<div class="quiz-number">'
                f'QUESTION {index + 1} / {total}'
                f'</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                f'<div class="quiz-question">'
                f'{question["question"]}'
                f'</div>',
                unsafe_allow_html=True
            )

            answer = st.radio(
                "Choose your answer",
                question["options"],
                key="answer_choice",
                label_visibility="collapsed"
            )

            if not st.session_state.answer_checked:

                if st.button(
                    "CHECK ANSWER ✓",
                    key=f"check_{index}"
                ):

                    with st.spinner(
                        "Checking..."
                    ):

                        result = check_answer_with_ai(
                            question["question"],
                            answer,
                            question["answer"]
                        )

                    st.session_state.last_result = result

                    st.session_state.answer_checked = True

                    if result["correct"]:

                        st.session_state.score += 1

                    else:

                        st.session_state.wrong_questions.append(
                            {
                                "question":
                                    question["question"],

                                "answer":
                                    question["answer"],

                                "student_answer":
                                    answer
                            }
                        )

                    st.rerun()


            if st.session_state.answer_checked:

                result = st.session_state.last_result

                if result["correct"]:

                    st.markdown(
                        f"""
                        <div class="correct-box">

                        <b>✓ Correct!</b>

                        <br><br>

                        {result["explanation"]}

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:

                    st.markdown(
                        f"""
                        <div class="wrong-box">

                        <b>✗ Not quite!</b>

                        <br><br>

                        {result["explanation"]}

                        <br><br>

                        <b>Correct answer:</b>
                        {question["answer"]}

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                if st.button(
                    "NEXT QUESTION →",
                    key=f"next_{index}"
                ):

                    if index + 1 >= total:

                        st.session_state.step = 6

                    else:

                        st.session_state.question_number += 1

                    st.session_state.answer_checked = False

                    st.session_state.last_result = None

                    st.rerun()


        # =================================================
        # STEP 6
        # =================================================

        elif st.session_state.step == 6:

            total = len(st.session_state.quiz)

            score = st.session_state.score

            percentage = (
                int((score / total) * 100)
                if total
                else 0
            )


            st.markdown(
                '<div class="notebook-heading">'
                'Your results 🎉'
                '</div>',
                unsafe_allow_html=True
            )


            st.markdown(
                f"""
                <div class="score-box">

                {score} / {total}

                <br>

                {percentage}%

                </div>
                """,
                unsafe_allow_html=True
            )


            # =================================================
            # ADAPTIVE DIFFICULTY
            # =================================================

            if percentage >= 80:

                if st.session_state.difficulty == "Easy":

                    new_difficulty = "Medium"

                elif st.session_state.difficulty == "Medium":

                    new_difficulty = "Hard"

                else:

                    new_difficulty = "Hard"

            elif percentage < 60:

                if st.session_state.difficulty == "Hard":

                    new_difficulty = "Medium"

                elif st.session_state.difficulty == "Medium":

                    new_difficulty = "Easy"

                else:

                    new_difficulty = "Easy"

            else:

                new_difficulty = (
                    st.session_state.difficulty
                )


            st.session_state.difficulty = new_difficulty


            st.markdown(
                f"""
                <div class="notebook-text">

                StudyAI will adjust your next quiz to:

                <br><br>

                <b>{new_difficulty}</b>

                </div>
                """,
                unsafe_allow_html=True
            )


            # =================================================
            # REVIEW
            # =================================================

            if st.session_state.wrong_questions:

                if st.button(
                    "CREATE MY REVIEW ✨",
                    key="create_review"
                ):

                    with st.spinner(
                        "StudyAI is making your review..."
                    ):

                        review = generate_review(
                            st.session_state.wrong_questions,
                            st.session_state.subject
                        )

                    st.session_state.review = review

                    st.rerun()


                if st.session_state.review:

                    st.markdown(
                        '<div class="notebook-heading">'
                        'StudyAI review 📚'
                        '</div>',
                        unsafe_allow_html=True
                    )

                    review_html = (
                        st.session_state.review
                        .replace("\n", "<br>")
                    )

                    st.markdown(
                        f"""
                        <div class="notebook-text">

                        {review_html}

                        </div>
                        """,
                        unsafe_allow_html=True
                    )


            # =================================================
            # NEW QUIZ
            # =================================================

            if st.button(
                "START NEW QUIZ ↻",
                key="new_quiz"
            ):

                st.session_state.step = 1

                st.session_state.name = ""

                st.session_state.subject = ""

                st.session_state.notes = ""

                st.session_state.quiz = []

                st.session_state.question_number = 0

                st.session_state.score = 0

                st.session_state.wrong_questions = []

                st.session_state.answer_checked = False

                st.session_state.last_result = None

                st.session_state.review = ""

                st.session_state.difficulty = "Easy"

                st.rerun()