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
    if 'show_final_practice' not in st.session_state:
        st.session_state.show_final_practice = False
    if 'previous_incorrect' not in st.session_state:
        st.session_state.previous_incorrect = False
    if 'completed' not in st.session_state:
        st.session_state.completed = False
    if 'final_essay_submitted' not in st.session_state:
        st.session_state.final_essay_submitted = False
    if 'original_essay' not in st.session_state:
        st.session_state.original_essay = ""

    if st.session_state.completed:
        st.success("Great job correcting all the errors! Now, try to rewrite your essay incorporating all the corrections.")
        
        # Display original essay in a container with a header
        st.subheader("Your Original Essay:")
        st.write(st.session_state.original_essay)
        
        st.subheader("Your Revised Essay:")
        final_essay = st.text_area("Enter your revised essay here:", height=200)
        
        if st.button("Submit Final Essay"):
            st.session_state.final_essay_submitted = True
            st.success("Congratulations! You've completed the exercise. Your writing skills are improving!")
            
        if st.button("Reset and Start Over"):
            st.session_state.clear()
            st.rerun()
        return

    # Essay input
    essay_text = st.text_area("Paste your Spanish essay here:", height=200)

    if st.button("Submit") or st.session_state.error_feedback:
        # Store original essay when first submitted
        if not st.session_state.error_feedback:
            st.session_state.original_essay = essay_text
            st.session_state.error_feedback = process_essay(essay_text)
            st.session_state.current_error_index = 0
            st.session_state.current_attempt = 1

        # Get current error
        current_errors = st.session_state.error_feedback
        if isinstance(current_errors, dict):
            current_errors = [current_errors]
        
        # Check if there are any errors
        if not current_errors or len(current_errors) == 0:
            st.success("I didn't find any grammatical errors in your essay. Impressive! Feel free to submit another essay if you'd like more practice.")
            if st.button("Reset and Start Over"):
                st.session_state.clear()
                st.rerun()
            return
        
        if st.session_state.current_error_index < len(current_errors):
            error = current_errors[st.session_state.current_error_index]
            
            # If we have a success message from previous correction, show it first
            if hasattr(st.session_state, 'success_message'):
                st.success(st.session_state.success_message)
                st.write(st.session_state.next_error)
                del st.session_state.success_message
                del st.session_state.next_error
            else:
                # Only display current error if we're not showing a previous success message
                st.write(f"Error identified: {error['line_1']}")
            
            # If we're showing a response, display it before the next input
            if st.session_state.show_response:
                st.write(st.session_state.current_response)
                
                # Show final practice if needed
                if st.session_state.show_final_practice:
                    final_practice = st.text_input(
                        "Please rewrite the sentence with the correction explained above:",
                        key=f"final_practice_{st.session_state.current_error_index}"
                    )
                    if st.button("Submit final practice", key=f"submit_final_{st.session_state.current_error_index}"):
                        correct_response = check_response(error, final_practice)
                        if 'yes' in correct_response.strip().lower():
                            if st.session_state.current_error_index < len(current_errors) - 1:
                                st.session_state.current_error_index += 1
                                st.session_state.current_attempt = 1
                                st.session_state.show_final_practice = False
                                st.session_state.show_response = False
                                st.session_state.previous_incorrect = False
                                st.rerun()
                            else:
                                st.session_state.completed = True
                                st.rerun()
                        else:
                            st.error("That's not quite right. Please review the explanation and try again.")
                    return
            
            # Don't show input if we're in final practice mode
            if not st.session_state.show_final_practice:
                # Show "Not quite..." message if previous attempt was incorrect
                if st.session_state.previous_incorrect:
                    st.write("Try again with the hint above.")
                
                # Handle current attempt
                prompt_text = "Try correcting the error above:"
                if st.session_state.current_attempt == 2:
                    prompt_text = "Let's try one more time with the hint above:"
                
                user_correction = st.text_input(
                    prompt_text,
                    key=f"correction_{st.session_state.current_error_index}_{st.session_state.current_attempt}"
                )
                
                if st.button("Submit correction", key=f"submit_{st.session_state.current_error_index}_{st.session_state.current_attempt}"):
                    correct_response = check_response(error, user_correction)
                    
                    if 'yes' in correct_response.strip().lower():
                        if st.session_state.current_error_index < len(current_errors) - 1:
                            # Store success message and next error in session state
                            st.session_state.success_message = error[f'response_{st.session_state.current_attempt}_correct']
                            next_error = current_errors[st.session_state.current_error_index + 1]
                            st.session_state.next_error = f"Error identified: {next_error['line_1']}"
                            
                            # Update index and attempt counters
                            st.session_state.current_error_index += 1
                            st.session_state.current_attempt = 1
                            
                            st.rerun()
                        else:
                            st.session_state.completed = True
                            st.rerun()
                    else:
                        st.session_state.current_response = error[f'response_{st.session_state.current_attempt}_incorrect']
                        st.session_state.show_response = True
                        st.session_state.previous_incorrect = True
                        if st.session_state.current_attempt < 2:
                            st.session_state.current_attempt += 1
                        else:
                            # Immediately show full correction with proper line breaks
                            st.session_state.current_response = (
                                "That was a good try, but there's still an issue.\n\n"
                                f"Your sentence:\n{error['error_orig']}\n\n"
                                f"Correct version:\n{error['error_corrected']}\n\n"
                                f"Explanation:\n{error['explanation']}"
                            )
                            st.session_state.show_final_practice = True
                            st.session_state.previous_incorrect = False
                        st.rerun()

    # Reset button at bottom of page
    if st.button("Reset and Start Over"):
        st.session_state.clear()
        st.rerun()


if __name__ == "__main__":
    main()
