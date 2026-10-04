import json
import os
import tinker
import numpy as np
import time
import tinker.types as types
from tinker_cookbook.renderers import get_renderer
from tinker_cookbook import weights, model_info
from tinker_cookbook.supervised.common import datum_from_model_input_weights
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = "You are a meal planning assistant. Suggest exactly 3 Indian dishes separated by newlines."

# Ensure TINKER_API_KEY is loaded from your .env file
TINKER_API_KEY = os.getenv("TINKER_API_KEY")

# 1. Initialize the LoRA client on Tinker for gpt-oss-20b
service_client = tinker.ServiceClient()

training_client = service_client.create_lora_training_client(
    base_model="openai/gpt-oss-20b", 
    rank=16
)

# Fetch the tokenizer using the updated method
tokenizer = training_client.get_tokenizer()

# 2. Setup the renderer for gpt-oss using the explicitly fetched tokenizer
renderer = get_renderer(model_info.get_recommended_renderer_name("openai/gpt-oss-20b"), tokenizer)

# 3. Load the synthetic dataset
with open("train.jsonl", "r") as f:
    dataset = [json.loads(line) for line in f]

def to_datum(item):
    prompt_msgs = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": item["instruction"]},
    ]

    # Render to text first, then encode -> guaranteed list[int]
    prompt_text = tokenizer.apply_chat_template(
        prompt_msgs, add_generation_prompt=True, tokenize=False
    )
    prompt_ids = tokenizer.encode(prompt_text, add_special_tokens=False)
    completion_ids = tokenizer.encode(item["output"], add_special_tokens=False)
    if tokenizer.eos_token_id is not None:
        completion_ids.append(tokenizer.eos_token_id)

    all_ids = prompt_ids + completion_ids
    weights = [0.0] * len(prompt_ids) + [1.0] * len(completion_ids)

    return types.Datum(
        model_input=types.ModelInput.from_ints(all_ids[:-1]),
        loss_fn_inputs={
            "target_tokens": types.TensorData.from_numpy(np.array(all_ids[1:], dtype=np.int64)),
            "weights": types.TensorData.from_numpy(np.array(weights[1:], dtype=np.float32)),
        },
    )

# 4. Training Hyperparameters
batch_size = 4
epochs = 3
lr = 1e-4

steps_per_epoch = -(-len(dataset) // batch_size)

print("Starting LoRA fine-tuning on Tinker...")

# 5. The Training Loop
for epoch in range(epochs):
    total_loss, total_tokens = 0.0, 0
    for step, i in enumerate(range(0, len(dataset), batch_size), start=1):
        t0 = time.time()
        data = [to_datum(item) for item in dataset[i:i + batch_size]]
        print(f"[e{epoch+1} s{step}/{steps_per_epoch}] built batch, submitting...", flush=True)

        fwdbwd_future = training_client.forward_backward(data, "cross_entropy")
        optim_future = training_client.optim_step(types.AdamParams(learning_rate=lr))

        result = fwdbwd_future.result(timeout=600)
        optim_future.result(timeout=600)

        total_loss += result.metrics["loss:sum"]
        total_tokens += sum(float(np.sum(d.loss_fn_inputs["weights"].to_numpy())) for d in data)
        print(f"[e{epoch+1} s{step}/{steps_per_epoch}] done in {time.time()-t0:.1f}s", flush=True)

    print(f"Epoch {epoch+1}/{epochs} | avg loss/token: {total_loss/total_tokens:.4f}", flush=True)



# 6. Export weights for sampling
print("\nTraining complete.")
print("Preparing adapter for export...")

sampler_path = (
    training_client
    .save_weights_for_sampler(name="mom-chef-v1")
    .result()
    .path
)

print(f"Tinker sampler weights: {sampler_path}")

# 7. Download adapter weights locally
# adapter_dir = weights.download(
#     tinker_path=sampler_path,
#     output_dir="out/adapter_raw",
# )

# print(f"Raw adapter downloaded to: {adapter_dir}")

# 8. Build standard PEFT LoRA adapter
# ============================================================

# weights.build_lora_adapter(
#     base_model="openai/gpt-oss-20b",
#     adapter_path=adapter_dir,
#     output_path="out/peft_adapter",
# )

print("\nPEFT adapter created successfully!")
print("Adapter location: out/peft_adapter")

# Epoch 1/3 | avg loss/token: 1.2875
# Epoch 2/3 | avg loss/token: 0.7259
# Epoch 3/3 | avg loss/token: 0.4878
# Tinker sampler weights: tinker://320f2157-8df7-5b5b-bf0f-b1cc6a083530:train:0/sampler_weights/mom-chef-v1
# Creating checkpoint archive for run id: 320f2157-8df7-5b5b-bf0f-b1cc6a083530:train:0 checkpoint id: sampler_weights/mom-chef-v1