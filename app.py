import streamlit as st
import spacy
import random
from collections import Counter
from pypdf import PdfReader

# ---------------- MODEL ----------------
@st.cache_resource
def load_model():
    return spacy.load("en_core_web_sm")

nlp = load_model()

# ---------------- PDF TEXT ----------------
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# ---------------- DIFFICULTY ----------------
def get_difficulty(sentence):
    words = len(sentence.split())

    if words < 10:
        return "low"
    elif words < 20:
        return "medium"
    else:
        return "high"

# ---------------- MCQ GENERATOR ----------------
def generate_mcqs(text, num_questions=5, level="medium"):

    if not text:
        return []

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]

    # filter by level
    filtered = [s for s in sentences if get_difficulty(s) == level]

    # fallback if not enough
    if len(filtered) < 2:
        filtered = sentences

    selected = random.sample(filtered, min(num_questions, len(filtered)))

    mcqs = []

    for sentence in selected:

        sent_doc = nlp(sentence)

        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        if len(nouns) < 2:
            continue

        answer = Counter(nouns).most_common(1)[0][0]

        question = sentence.replace(answer, "________", 1)

        distractors = list(set(nouns) - {answer})

        while len(distractors) < 3:
            distractors.append("None of the above")

        random.shuffle(distractors)

        choices = [answer] + distractors[:3]
        random.shuffle(choices)

        mcqs.append({
            "question": question,
            "choices": choices,
            "answer": answer,
            "difficulty": get_difficulty(sentence)
        })

    return mcqs


# ---------------- SESSION STATE ----------------
if "submitted" not in st.session_state:
    st.session_state.submitted = False

if "mcqs" not in st.session_state:
    st.session_state.mcqs = []

# ---------------- UI ----------------
st.title("🧠 AI MCQ Quiz Generator")

uploaded_file = st.file_uploader("📄 Upload PDF", type=["pdf"])
text_input = st.text_area("✍️ OR Enter Text", height=200)

num_questions = st.slider("🎯 Number of Questions", 1, 20, 5)

level = st.selectbox(
    "🎚️ Choose Difficulty Level",
    ["low", "medium", "high"]
)

# ---------------- TEXT SOURCE ----------------
text = ""

if uploaded_file:
    text = extract_text_from_pdf(uploaded_file)
    st.success("PDF Loaded Successfully!")

elif text_input:
    text = text_input

# ---------------- GENERATE ----------------
if st.button("Generate MCQs"):

    st.session_state.mcqs = generate_mcqs(text, num_questions, level)
    st.session_state.submitted = False

    if not st.session_state.mcqs:
        st.warning("Not enough content to generate MCQs.")

# ---------------- QUIZ MODE ----------------
if st.session_state.mcqs:

    st.subheader("📘 Quiz Mode")

    for i, mcq in enumerate(st.session_state.mcqs):

        st.write(f"### Q{i+1}")
        st.write(mcq["question"])

        st.radio(
            "Select your answer:",
            mcq["choices"],
            key=f"q_{i}",
            disabled=st.session_state.submitted
        )

# ---------------- SUBMIT ----------------
if st.session_state.mcqs and not st.session_state.submitted:

    if st.button("Submit Answers"):

        score = 0

        for i, mcq in enumerate(st.session_state.mcqs):

            if st.session_state[f"q_{i}"] == mcq["answer"]:
                score += 1

        st.session_state.score = score
        st.session_state.total = len(st.session_state.mcqs)
        st.session_state.submitted = True

# ---------------- RESULT ----------------
if st.session_state.submitted:

    st.success(f"🎯 Your Score: {st.session_state.score} / {st.session_state.total}")

    st.subheader("📊 Review Answers")

    for i, mcq in enumerate(st.session_state.mcqs):

        st.write(f"### Q{i+1}")
        st.write(mcq["question"])

        user_ans = st.session_state[f"q_{i}"]
        correct_ans = mcq["answer"]

        for option in mcq["choices"]:

            if option == correct_ans:
                st.markdown(f"🟢 **{option} (Correct Answer)**")

            elif option == user_ans and user_ans != correct_ans:
                st.markdown(f"🔴 **{option} (Your Answer)**")

            else:
                st.write(option)

        st.divider()
