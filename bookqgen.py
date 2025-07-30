import json
import google.generativeai as genai

# Initialize the Google Generative AI client with your API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def is_valid_json(response_text):
    """Check if the response text is valid JSON."""
    try:
        json.loads(response_text)
        return True
    except json.JSONDecodeError:
        return False


def remove_last_incomplete_question(response_text):
    """Remove the last question which would have started off with '{' and then close the JSON properly."""
    last_brace = response_text.rfind('{')

    # If we find an incomplete question, truncate the response text before that last question
    if last_brace != -1:
        response_text = response_text[:last_brace]

    # Ensure the JSON is closed correctly with brackets
    response_text = response_text.rstrip(', ')  # Remove any trailing commas or spaces
    response_text += ']'

    return response_text


def generate_mcq_for_chapter(chapter_name, pdf_file):
    """Generate MCQs for a chapter from the PDF."""
    prompt = f"""
    Extract all MCQ questions in JSON format for the chapter titled '{chapter_name}' from this textbook PDF.
    Each MCQ should have the following structure:
    {{
        "question": "string",
        "options": ["string", "string", "string", "string"],
        "answer": "string"
    }}
    """

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([prompt, pdf_file], generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
    ))

    # Debug: Print the raw response
    response_text = response.text
    print(f"Response for {chapter_name}: {response_text}")

    # Remove the last incomplete question and close JSON correctly
    response_text = remove_last_incomplete_question(response_text)

    try:
        mcq_list = json.loads(response_text)
        print(f"Successfully decoded JSON for chapter {chapter_name}.")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON for chapter {chapter_name}. Response was: {response_text}")
        return []  # Return an empty list if parsing fails

    return mcq_list


def generate_quiz_from_pdf(pdf_file, chapters, book_name):
    """Generate a quiz JSON file from the PDF containing multiple chapters."""
    quiz = {
        "book_name": book_name,
        "chapters": []
    }

    for chapter in chapters:
        mcqs = generate_mcq_for_chapter(chapter, pdf_file)

        # Debug: Print the generated MCQs
        print(f"MCQs for {chapter}: {mcqs}\n")

        # Menu-driven decision: 'a' to add, 'r' to rerun
        while True:
            user_input = input(f"Do you want to 'add' (a) these MCQs or 'rerun' (r) for {chapter}? ").lower()
            if user_input == 'a':
                # Append chapter with its MCQs to the quiz
                quiz["chapters"].append({
                    "chapter_name": chapter,
                    "mcqs": mcqs
                })
                break
            elif user_input == 'r':
                mcqs = generate_mcq_for_chapter(chapter, pdf_file)  # Regenerate MCQs
            else:
                print("Invalid input, please choose 'a' to add or 'r' to rerun.")

    # Debug: Print the entire quiz JSON before saving
    print("Final Quiz JSON:\n", json.dumps(quiz, indent=4))

    # Save the quiz as a JSON file
    with open('quiz5.json', 'w') as outfile:
        json.dump(quiz, outfile, indent=4)


# Example usage
pdf_file = genai.get_file(name="bh4y84tyh6ut")  # Replace with actual file fetching logic if needed
chapters = ['Medieval History']
book_name = 'Disha PYQs'

generate_quiz_from_pdf(pdf_file, chapters, book_name)
