from chat_completion import send_openrouter_request
import os

def test_send_openrouter_request():
    print("Starting test_send_openrouter_request function")
    try:
        print(f"OPENROUTER_API_KEY is {'set' if os.environ.get('OPENROUTER_API_KEY') else 'not set'}")
        sample_message = "Tell me about Jonathan Brockman's passion for AI."
        print(f"Sample message: {sample_message}")
        
        print("Calling send_openrouter_request function")
        response = send_openrouter_request(sample_message)
        
        print("Response received:")
        print(response)
        return True
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {e.args}")
        return False

if __name__ == "__main__":
    print("Starting test script")
    success = test_send_openrouter_request()
    if success:
        print("Test passed successfully!")
    else:
        print("Test failed.")
    print("Test script completed")
