import streamlit as st
import json
import random
from google import genai


# ==========================================
# GEMINI CONNECTION
# ==========================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# ==========================================
# PAGE SETUP
# ==========================================

st.set_page_config(
    page_title="StudyAI",
    page_icon="🧠"
)


# ==========================================
# SESSION STATE
# ==========================================

if "step" not in st.session_state:
    st.session_state.step = 1

if "score" not in st.session_state:
    st.session_state.score = 0

if "question_number" not in st.session_state:
    st.session_state.question_number = 0

if "wrong_questions" not in st.session_state:
    st.session_state.wrong_questions = []

if "quiz" not in st.session_state:
    st.session_state.quiz = []


# ==========================================
# TITLE
# ==========================================

st.title("🧠 StudyAI")
st.write("Your AI-powered study assistant")


# ==========================================
# GENERATE QUESTIONS
# ==========================================

def generate_questions(notes, subject, difficulty):

    if difficulty == "Easy":

        difficulty_instructions = """
Focus mainly on basic facts, definitions,
names, and simple recall.

Keep the questions straightforward.
"""

    elif difficulty == "Medium":

        difficulty_instructions = """
Test understanding.

Ask about relationships, causes, effects,
differences, and connections between ideas
in the notes.
"""

    else:

        difficulty_instructions = """
Make the questions challenging.

Ask the student to apply ideas, analyze situations,
compare concepts, or reason about what would happen.

The answer must still be possible using ONLY the notes.
Do not require outside knowledge.
"""

    prompt = f"""
You are StudyAI, an AI study assistant.

Subject:
{subject}

Difficulty:
{difficulty}

Student's study notes:
{notes}

{difficulty_instructions}

Create exactly 5 multiple-choice questions.

IMPORTANT:
- Use ONLY information from the student's notes.
- Do not invent facts.
- Every question must have exactly 4 choices.
- Only ONE choice can be correct.
- Make incorrect choices believable.
- Make the questions appropriate for a high school student.

Return ONLY valid JSON.

Use exactly this format:

[
  {{
    "question": "Question here",
    "A": "Choice here",
    "B": "Choice here",
    "C": "Choice here",
    "D": "Choice here",
    "answer": "A"
  }}
]

Do not write anything before or after the JSON.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",  # 👈 Updated model to 3.6
        contents=prompt
    )

    return json.loads(response.text)


# ==========================================
# AI REVIEW
# ==========================================

def generate_review(wrong_questions, subject):

    wrong_text = ""

    for question in wrong_questions:

        correct_answer = question["answer"]

        wrong_text += f"""
Question:
{question["question"]}

Correct answer:
{correct_answer}) {question[correct_answer]}

"""

    review_prompt = f"""
You are StudyAI, a friendly AI tutor.

The student is studying:
{subject}

The student got these questions wrong:

{wrong_text}

For each question:

1. Explain the concept in very simple terms.
2. Explain why the correct answer is correct.
3. Give one short memory tip.

Keep the explanations short and suitable
for a high school student.

Do NOT use Markdown.
Do NOT use ###.
Do NOT use **.
Do NOT use ---

Use this format:

QUESTION 1

Correct Answer:
Simple Concept:
Why It's Correct:
Memory Tip:

QUESTION 2

Correct Answer:
Simple Concept:
Why It's Correct:
Memory Tip:
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",  # 👈 Updated model to 3.6
        contents=review_prompt
    )

    return response.text


# ==========================================
# STEP 1 — NAME
# ==========================================

if st.session_state.step == 1:

    st.subheader("👋 Let's get started!")

    name = st.text_input(
        "What's your name?"
    )

    if st.button(
        "Continue",
        key="btn_step_1"
    ):

        if name.strip():

            st.session_state.name = name.strip()
            st.session_state.step = 2

            st.rerun()

        else:

            st.warning(
                "Please enter your name."
            )


# ==========================================
# STEP 2 — SUBJECT
# ==========================================

elif st.session_state.step == 2:

    st.write(
        "Hello",
        st.session_state.name + "!"
    )

    subject = st.text_input(
        "What subject do you want to study?"
    )

    if st.button(
        "Continue",
        key="btn_step_2"
    ):

        if subject.strip():

            st.session_state.subject = subject.strip()
            st.session_state.step = 3

            st.rerun()

        else:

            st.warning(
                "Please enter a subject."
            )


# ==========================================
# STEP 3 — NOTES
# ==========================================

elif st.session_state.step == 3:

    st.write(
        "Great! Let's study",
        st.session_state.subject + "!"
    )

    notes = st.text_area(
        "📝 Paste your study notes here:",
        height=250
    )

    if st.button(
        "Continue",
        key="btn_step_3"
    ):

        if notes.strip():

            st.session_state.notes = notes.strip()
            st.session_state.step = 4

            st.rerun()

        else:

            st.warning(
                "Please enter your study notes."
            )


# ==========================================
# STEP 4 — DIFFICULTY
# ==========================================

elif st.session_state.step == 4:

    st.subheader(
        "🎯 Choose your starting difficulty"
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    if st.button(
        "🤖 Generate Quiz",
        key="btn_step_4"
    ):

        st.session_state.difficulty = difficulty

        with st.spinner(
            "StudyAI is creating your quiz..."
        ):

            try:

                quiz = generate_questions(
                    st.session_state.notes,
                    st.session_state.subject,
                    difficulty
                )

                random.shuffle(quiz)

                st.session_state.quiz = quiz
                st.session_state.question_number = 0
                st.session_state.score = 0
                st.session_state.wrong_questions = []

                st.session_state.step = 5

                st.rerun()

            except Exception as e:

                st.error(
                    "Something went wrong while creating the quiz."
                )

                st.code(str(e))


# ==========================================
# STEP 5 — QUIZ
# ==========================================

elif st.session_state.step == 5:

    quiz = st.session_state.quiz

    question_number = st.session_state.question_number

    question = quiz[question_number]

    st.subheader(
        f"Question {question_number + 1} of {len(quiz)}"
    )

    st.write(question["question"])

    choices = {
        "A": question["A"],
        "B": question["B"],
        "C": question["C"],
        "D": question["D"]
    }

    # --------------------------------------
    # BEFORE ANSWER IS CHECKED
    # --------------------------------------

    if not st.session_state.get("answer_checked", False):

        answer = st.radio(
            "Choose your answer:",
            list(choices.keys()),
            format_func=lambda letter:
                f"{letter}) {choices[letter]}",
            key=f"answer_{question_number}"
        )

        if st.button(
            "Check Answer",
            key=f"check_{question_number}"
        ):

            st.session_state.selected_answer = answer

            if answer == question["answer"]:

                st.session_state.last_result = "correct"
                st.session_state.score += 1

            else:

                st.session_state.last_result = "wrong"

                st.session_state.wrong_questions.append(
                    question
                )

            st.session_state.answer_checked = True

            st.rerun()


    # --------------------------------------
    # AFTER ANSWER IS CHECKED
    # --------------------------------------

    else:

        selected_answer = (
            st.session_state.selected_answer
        )

        if st.session_state.last_result == "correct":

            st.success("✅ Correct!")

        else:

            st.error("❌ Wrong!")

            correct_answer = question["answer"]

            st.write(
                "Correct answer:",
                f"{correct_answer})",
                question[correct_answer]
            )

        # ----------------------------------
        # NEXT QUESTION BUTTON
        # ----------------------------------

        if st.button(
            "Next Question →",
            key=f"next_{question_number}"
        ):

            st.session_state.question_number += 1

            st.session_state.answer_checked = False

            if (
                st.session_state.question_number
                >= len(quiz)
            ):

                st.session_state.step = 6

            st.rerun()

# ==========================================
# STEP 6 — RESULTS & AI REVIEW
# ==========================================

elif st.session_state.step == 6:

    st.subheader("🎉 Quiz Completed!")
    st.write(f"Great job, {st.session_state.name}!")
    
    # Display final score
    total_questions = len(st.session_state.quiz)
    st.metric(label="Your Final Score", value=f"{st.session_state.score} / {total_questions}")

    # Generate custom feedback depending on performance
    if st.session_state.score == total_questions:
        st.balloons()
        st.success("Perfect score! You mastered this material.")
    else:
        st.info("Let's review the items you missed with StudyAI.")
        
        # Trigger the AI Tutor custom review session
        with st.spinner("🤖 StudyAI is preparing your personalized review text..."):
            try:
                review_report = generate_review(
                    st.session_state.wrong_questions,
                    st.session_state.subject
                )
                st.text_area("Your Custom Study Guide:", value=review_report, height=400)
            except Exception as review_err:
                st.error("Could not construct your personalized review guide.")
                st.code(str(review_err))

    # Reset button to test on another topic or difficulty
    if st.button("🔄 Start a New Session", key="btn_restart"):
        st.session_state.step = 1
        st.session_state.score = 0
        st.session_state.question_number = 0
