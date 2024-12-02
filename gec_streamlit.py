import openai
import streamlit as st
import re

# Initialize OpenAI API key
openai.api_key = 'your-openai-api-key'

# Function to process essay through GPT-4o (place your GPT-4o logic here)
def process_essay(essay_text):
    # Call the GPT-4o model to find and explain errors
    response = openai.Completion.create(
        engine="text-davinci-004",  # As an example
        prompt = '''You are a helpful assitant helping the teacher of a Spanish 1 course. You are writing corrections \
        for a student whose native language is English. You want to provide your students with feedback about mistakes \
        in their writing. Given an original essay written by a student, please correct any obvious errors in the essay, \
        and explain to the student why you made the corrections you made. Explain the differences between them in terms \
        of grammar in a way a student can understand.
        
        Your goal is to provide feedback in a way that can be automatically presented to students, and that gives the \
        students an opportunity to correct their own mistakes. Please format your response as in JSON format containing \
        the following basic elements. Don't include these descriptions in your output, just use them as examples of \
        what you need to generate:
        
        error_orig = The original sentence containting the error.
        error_corrected = The corrected version of the sentence that corrected the specific error being presented only.
        line_1 = The first text presented to the student. This should tell the student which sentence the error is in and provide a hint as to what the error is and ask the student to fix it.
        response_1_correct = The text to be presented to students if they were able to successfully correct the error. This should be encouraging and summarize the correction.
        response_1_incorrect = To be presented to student if they are unable to correct their mistake the first time they try. This should provide a little more information about the error in question and ask the student to correct it.
        response_2_correct = To be presented to student if they are able to correct the error on their second try. Again, this should be encouraging and summarize the error and correction. 
        response_2_incorrect = Used if the student still can't correct the error themselves. This should explain the error and the correction in detail.
        explanation: A final explanation of the correction to be used as the last output to a student who is unable to self-correct.
        
        The JSON you generate will be used by a script that presents feedback to students one step at a time. \
        The student will be asked to self-correct, then if unable to do so, provided a bit more info and asked again to \
        self-correct. If still unable to do so, the full error and its correction will be explained to the student. \
        So keep these goals in mind when generating your output.
        
        If there is more than one correction in a sentence, make sure to create a JSON formatted dictionary for each \
        correction you identify in the sentence pair.

        Please provide your responses in English. Put your JSON output between <JSON_out> tags.
        
        <essay_text>
        {essay_text}
        </essay_text>
''',

        #prompt=f"Please analyze the following Spanish text for beginner-level Spanish errors, focusing on grammar and basic vocabulary. Provide up to 5 significant errors that affect comprehension and explain each error:\n\n{essay_text}\n\n",
        max_tokens=5000,
        temperature=0.5
    )

    output = response.choices[0].text.strip()

    vals = re.findall(r'<JSON_out>(.*?)</JSON_out>', output)
    return vals[0]

def check_response(error, user_correction):
    response = openai.Completion.create(
        engine="text-davinci-004",  # As an example
        prompt= f'''You are a helpful assitant helping the teacher of a Spanish 1 course. \
        Given the following sentence containing and error, a previously identified target correction, and the student's \
        correction attempt, please identify if the student successfully corrected the error or not. Your response \
        should be a simple "yes" or "no" between <response> tags.
        
        <error_sentence>
        {error['error_orig']}
        </error_sentence>
        
        <target_correction>
        {error['error_corrected']}
        </target_correction>
        
        <student_correction>
        {user_correction}
        </student_correction>
        ''',
        max_tokens=100,
        temperature=0.5
    )

    output = response.choices[0].text.strip()

    vals = re.findall(r'<response>(.*?)</response>', output)
    return vals[0]

# Main Streamlit app
def main():
    st.title("Corregram: Spanish Writing Improvement Tool")

    # Essay input
    essay_text = st.text_area("Paste your Spanish essay here:", height=200)

    if st.button("Submit"):
        # Process the essay and get error feedback from GPT-4o
        error_feedback = process_essay(essay_text)

        for error in error_feedback:
            st.session_state['attempts'] = 0  # Reset attempts for each error
            this_error = error['line_1']
            st.write(f"Error identified: {this_error}")

            # Allow up to 2 attempts to correct each error
            for i in range(2):
                index = i + 1
                user_correction = st.text_input("Try correcting the error above:")
                correct_response = check_response(error, user_correction)
                if 'yes' in correct_response.strip().lower():
                    success = error[f'response_{index}_correct']
                    st.success(success)
                    break
                else:
                    fail = error[f'response_{index}_incorrect']
                    st.warning(f"{fail}")
                    if index == 1:
                        st.warning("Try again!")

            else:  # If two attempts fail
                st.write(f"Your sentence: {error['error_orig']}")
                st.write(f"Correct version: {error['error_corrected']}")
                st.write(f"Explanation: {error['explanation']}")

        # Option to rewrite the essay and resubmit
        if st.button("If you would like to try again, Rewrite Essay & Resubmit"):
            st.session_state.clear()

if __name__ == "__main__":
    main()
