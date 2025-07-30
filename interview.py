import google.generativeai as genai

# Configure the API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")
transcripts_file = genai.get_file(name="dpiscjejycn9")  # Uploaded interview transcripts

# Initial context for the interview bot
prompt_context = (
    f"You are a strict UPSC interview bot. Use the uploaded file '{transcripts_file}' "
    "containing real UPSC interview transcripts for inspiration. Conduct a mock UPSC interview with the following rules:\n"
    "- Ask one question at a time.\n"
    "- Never answer your own questions.\n"
    "- Analyze responses critically, considering detail, technical accuracy, and communication skills.\n"
    "- Do not provide feedback after each question; feedback and scoring will be provided only after the entire interview.\n"
    "- Ask exactly 5 questions and conclude with an evaluation of performance."
)

# Helper function: Ask a question
def ask_question(question_number):
    global prompt_context
    question_prompt = prompt_context + f"\n\nAsk Question {question_number}."
    question_response = model.generate_content([transcripts_file, question_prompt])
    return question_response.text.strip()

# Helper function: Final evaluation of all responses
def evaluate_all_responses(responses):
    feedback_prompt = (
        f"Here are the interviewee's responses:\n\n"
        f"{responses}\n\n"
        "Critically evaluate these responses based on technical accuracy, detail, and communication. "
        "Provide a score out of 10 and constructive feedback, highlighting strengths and areas for improvement."
    )
    feedback_response = model.generate_content([transcripts_file, feedback_prompt])
    return feedback_response.text.strip()

# Main interview function
def conduct_interview():
    global prompt_context
    responses = []
    print("Starting the UPSC interview simulation...\n")

    for i in range(1, 6):  # Conduct a 5-question interview
        # Ask the question
        question = ask_question(i)
        print(f"Question {i}: {question}")

        # Get user response
        user_response = input(f"Your Answer to Question {i}: ").strip()
        responses.append(f"Q{i}: {question}\nA{i}: {user_response}")

        # Update context with Q&A (but do not give feedback yet)
        prompt_context += f"\n\nQ{i}: {question}\nA{i}: {user_response}"

    # Provide final evaluation after all questions
    all_responses = "\n".join(responses)
    final_feedback = evaluate_all_responses(all_responses)
    print("\n=== Final Interview Feedback ===\n")
    print(final_feedback)

# Run the program
if __name__ == "__main__":
    conduct_interview()
