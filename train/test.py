import os
import tinker
from dotenv import load_dotenv
from tinker_cookbook.renderers import get_renderer


load_dotenv()

SAMPLER_PATH = os.getenv("TINKER_SAMPLER_PATH", "sampler_weights/mom-chef-v1")

def run_test():
    print(f"Connecting to Tinker Cloud...\nTarget Adapter: {SAMPLER_PATH}\n")
    
    # 1. Initialize the Tinker client
    service_client = tinker.ServiceClient()
    sampler = service_client.create_sampling_client(model_path=SAMPLER_PATH)
    
    # 2. Fetch the tokenizer and set up the exact same renderer used for training
    tokenizer = sampler.get_tokenizer()
    renderer = get_renderer("role_colon", tokenizer)
    
    # 3. Define the input
    pantry_items = "thoda sa paneer bacha hai, aur palak, tamatar hain."
    
    # 4. Structure the prompt exactly like the training data. 
    messages = [
        {"role": "user", "content": pantry_items},
    ]
    
    # 5. Build the structured ModelInput (this creates the object with .chunks)
    model_input, _ = renderer.build_supervised_example(messages)
    
    print(f"Input: {pantry_items}")
    print("Generating suggestions...\n")
    print("--- Model Output ---")
    
    try:
        # 6. Pass the structured model_input instead of a raw string
        responses = sampler.sample(
            prompt=model_input,
            num_samples=1,
            sampling_params={"max_tokens": 100}
        ).result()
        
        # Extract and print the raw text
        # Extract the first generated sequence
        sequence = responses.sequences[0]
        
        # Decode the raw token IDs back into readable text
        try:
            text_output = tokenizer.decode(sequence.tokens, skip_special_tokens=True)
        except AttributeError:
            # If 'tokens' fails, print the object's available attributes so we can see exactly what Tinker provides
            attrs = [a for a in dir(sequence) if not a.startswith('_')]
            print(f"Debug - Available attributes on SampledSequence: {attrs}")
            text_output = ""
            
        print(text_output.strip())
        
        print("--------------------")
        
        # Quick validation check
        lines = [line for line in text_output.strip().split("\n") if line.strip()]
        if len(lines) == 3:
            print("✅ Success: The model strictly adhered to the 3-line format.")
        else:
            print(f"⚠️ Warning: The model returned {len(lines)} lines instead of 3.")
            
    except Exception as e:
        print(f"❌ Error communicating with Tinker: {e}")

if __name__ == "__main__":
    run_test()