import gradio as gr
import os
from groq import Groq
from gtts import gTTS
import tempfile
import random
import json

# Initialize the Groq client with API Key
def initialize_groq_client(api_key):
    return Groq(api_key=api_key)

API_KEY = API_KEY
client = initialize_groq_client(API_KEY)

def extract_subject_questions(subject):
    file_path = f"{subject.lower()}_questions.json"
    return extract_questions(file_path)

# Extract questions from JSON
def extract_questions(json_file_path):
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("The JSON file does not contain a list of questions.")
        return random.choice(data)
    except Exception as e:
        print(f"Error: {e}")
        return ""

# Transcribe audio
def transcribe_audio(audio_file):
    try:
        with open(audio_file, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_file, file.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                temperature=0.0
            )
        return transcription
    except Exception as e:
        return f"Error: {str(e)}"

# Text to speech generation
def generate_speech(text):
    try:
        tts = gTTS(text=text, lang='en', tld='co.in')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
            tts.save(tmp_audio.name)
            return tmp_audio.name
    except Exception as e:
        print(f"Error in generating speech: {e}")
        return None

# Behavior analysis
def assess_behavior(user_input):
    if "confidence" in user_input.lower():
        return "The response shows good confidence."
    elif "uncertain" in user_input.lower():
        return "The response indicates uncertainty. Consider clarifying your thoughts."
    elif "humble" in user_input.lower():
        return "The response shows humility and understanding."
    else:
        return "The response is neutral. The interviewee seems thoughtful."

# UPSC Interview Simulation
def simulate_upsc_interview(user_input, audio, chat_history, question_bank, question_index):
    response_text = ""
    audio_output = None

    if audio:
        transcription = transcribe_audio(audio)
        chat_history.append(("Interviewee (Audio)", transcription))
        user_input = transcription

    if user_input:
        chat_history.append(("Interviewee", user_input))
        behavior_feedback = assess_behavior(user_input)
        chat_history.append(("Interviewer", behavior_feedback))
        response_text = behavior_feedback
        print(question_bank)
        try:
            system_prompt = (
                f"You are a strict UPSC interview panelist assessing a candidate. "
                f"Respond professionally, focusing on the character and behavior of the candidate."
                f"But dont speak it out loud unless you feel that the behaviour of the candidate is extreme. The assessments should be in the form of small appreciations or comments about his behaviour, thats all."
                f"Ask follow-up questions based on their tone, confidence, and clarity of thought. Only for the first 2 to 3 questions."
                f"Then start asking questions from {question_bank} and ask follow up questions based on the answers the interviwee provides."
                f"Whenever you ask a follow-up question, make sure to take the answer from the interviewee. No need to rush to the next question."
                f"The follow up questions related to a single questions should not go beyond 1 question. If you are satisfied with the answers provided, appreciate the candidate and move to the next question."
                f"If you are not satisfied, then give your comments and move on to the next question."
                f"Current response: {user_input}.\nBehavior Feedback: {behavior_feedback}."
                f"The interview should end after 3 questions. Give your feedback on the interview to the candidate and say thank you politely."
            )

            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=300
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"Error generating response: {str(e)}"

        chat_history.append(("Interviewer", reply))
        response_text = reply
        question_index += 1
        audio_output = generate_speech(reply)

    return response_text, chat_history, audio_output, question_index

# Main App
def main():
    subject_list = ['economics', 'environment', 'technology', 'geography']

    def subject_selected(subject):
        return extract_subject_questions(subject), subject

    with gr.Blocks() as demo:
        gr.Markdown("## UPSC Interview Subject Selection")
        with gr.Tabs():
            with gr.Tab("Select Subject"):
                subject = gr.Dropdown(choices=subject_list, label="Select UPSC Optional Subject")
                next_button = gr.Button("Proceed to Interview")
                question_bank = gr.State("")

            with gr.Tab("Interview Simulation"):
                gr.Markdown("## UPSC Interview Simulation")
                chat_history = gr.State([])
                question_index = gr.State(0)

                audio_input = gr.Audio(label="Upload Voice Message", type="filepath")
                user_input = gr.Textbox(label="Your Answer Here")
                submit_button = gr.Button("Submit")
                output_text = gr.Textbox(label="Interviewer Response", interactive=False)
                chatbot = gr.Chatbot(label="UPSC Interview Conversation")
                audio_output = gr.Audio(label="Interviewer's Voice Reply", type="filepath")
                print(question_bank)
                def handle_interview(user_input, audio_input, chat_history, question_index, question_bank):
                    return simulate_upsc_interview(user_input, audio_input, chat_history, question_bank, question_index)

                submit_button.click(
                    handle_interview,
                    inputs=[user_input, audio_input, chat_history, question_index, question_bank],
                    outputs=[output_text, chatbot, audio_output, question_index],
                )

            next_button.click(
                subject_selected,
                inputs=[subject],
                outputs=[question_bank],
            )

    demo.launch(server_port=7860, share=False)


if __name__ == "__main__":
    main()
