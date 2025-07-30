import google.generativeai as genai


def generate_mcqs_from_text(text_content):
    # Replace with your Gemini API endpoint and API key

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
       Based on the following content, generate 4-25 multiple choice questions (MCQs). 
       Each MCQ should be in the following JSON format:
       {{
           "question": "string",
           "options": ["string", "string", "string", "string"],
           "answer": "string"
       }}
       Give only and only the json . Nothing else , no extra information or marker needed.
       The questions should be clear and informative. 
       Here is the content for generating MCQs:
       {text_content}
       """

    # Set the generation parameters

    # Make the API call to generate MCQs
    response = model.generate_content(prompt,generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
    ),)

    # Extract and return the generated content as JSON
    if response:
        return response.text
    else:
        raise Exception("No MCQs generated from the response.")

