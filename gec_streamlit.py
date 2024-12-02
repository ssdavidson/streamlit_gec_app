import openai
import streamlit as st
import re, json

# Initialize OpenAI API key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to process essay through GPT-4o (place your GPT-4o logic here)
def process_essay(essay_text):
    # Call the GPT-4o model to find and explain errors
    prompt = f'''You are writing corrections \
            for a student whose native language is English. You want to provide your students with feedback about mistakes \
            in their writing. Given an original essay written by a student, please correct any grammatical errors in the essay, \
            and explain to the student why you made the corrections you made. Explain the differences between them in terms \
            of grammar in a way a student can understand. Do not correct factual errors, only grammatical or semantic errors.

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
    '''
    response = openai.chat.completions.create(
        model="gpt-4o",  # As an example
        messages=[
            {"role": "system", "content": "You are a helpful assitant helping the teacher of a Spanish 1 course."},
            {"role": "user", "content": prompt},
        ],
    )

    output = response.choices[0].message.content.strip()

    vals = re.findall(r'(?<=<JSON_out>)([\s\S]*?)(?=</JSON_out>)', output)
    output = json.loads(vals[0].strip())
    return output

def check_response(error, user_correction):
    prompt = f'''Given the following sentence containing an error, a previously identified target correction, and the student's \
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
            '''
    response = openai.chat.completions.create(
        model='gpt-4o',
        messages=[
            {"role": "system", "content": "You are a helpful assitant helping the teacher of a Spanish 1 course."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=100,
        temperature=0.5
    )

    output = response.choices[0].message.content.strip()

    vals = re.findall(r'(?<=<response>)([\s\S]*?)(?=</response>)', output)
    output = vals[0].strip()
    return output

# Main Streamlit app
def main():
    st.title("Corregram: Spanish Writing Improvement Tool")
    
    # Initialize session state variables if they don't exist
    if 'current_error_index' not in st.session_state:
        st.session_state.current_error_index = 0
    if 'current_attempt' not in st.session_state:
        st.session_state.current_attempt = 1
    if 'error_feedback' not in st.session_state:
        st.session_state.error_feedback = None
    if 'show_response' not in st.session_state:
        st.session_state.show_response = False
    if 'current_response' not in st.session_state:
        st.session_state.current_response = ""

    # Essay input
    essay_text = st.text_area("Paste your Spanish essay here:", height=200)

    if st.button("Submit") or st.session_state.error_feedback:
        # Process the essay only if we haven't already
        if not st.session_state.error_feedback:
            st.session_state.error_feedback = process_essay(essay_text)
            st.session_state.current_error_index = 0
            st.session_state.current_attempt = 1

        # Get current error
        current_errors = st.session_state.error_feedback
        if isinstance(current_errors, dict):
            current_errors = [current_errors]
        
        if st.session_state.current_error_index < len(current_errors):
            error = current_errors[st.session_state.current_error_index]
            
            # Display current error
            st.write(f"Error identified: {error['line_1']}")
            
            # If we're showing a response, display it before the next input
            if st.session_state.show_response:
                st.write(st.session_state.current_response)
                st.session_state.show_response = False
            
            # Handle current attempt
            user_correction = st.text_input(
                "Try correcting the error above:",
                key=f"correction_{st.session_state.current_error_index}_{st.session_state.current_attempt}"
            )
            
            if st.button("Submit correction", key=f"submit_{st.session_state.current_error_index}_{st.session_state.current_attempt}"):
                correct_response = check_response(error, user_correction)
                
                if 'yes' in correct_response.strip().lower():
                    st.session_state.current_response = error[f'response_{st.session_state.current_attempt}_correct']
                    st.session_state.show_response = True
                    if st.session_state.current_error_index < len(current_errors) - 1:
                        st.session_state.current_error_index += 1
                        st.session_state.current_attempt = 1
                    else:
                        st.session_state.current_response += "\n\nYou've completed all corrections!"
                else:
                    st.session_state.current_response = error[f'response_{st.session_state.current_attempt}_incorrect']
                    st.session_state.show_response = True
                    if st.session_state.current_attempt < 2:
                        st.session_state.current_attempt += 1
                    else:
                        st.session_state.current_response += f"\n\nYour sentence: {error['error_orig']}\n"
                        st.session_state.current_response += f"Correct version: {error['error_corrected']}\n"
                        st.session_state.current_response += f"Explanation: {error['explanation']}"
                        if st.session_state.current_error_index < len(current_errors) - 1:
                            st.session_state.current_error_index += 1
                            st.session_state.current_attempt = 1
                        else:
                            st.session_state.current_response += "\n\nYou've completed all corrections!"
                st.rerun()

    # Reset button
    if st.button("Reset and Start Over"):
        st.session_state.clear()
        st.rerun()



if __name__ == "__main__":
    main()
