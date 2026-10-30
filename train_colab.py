# =============================================================================
# ResumeGrind: Bulletproof Llama 3.2 Fine-Tuning in Google Colab (Free T4 GPU)
# No manual file upload needed - paste and click "Run all"
# =============================================================================

# Step 1: Install Dependencies (Clean, pre-built wheels only - NO compiling xformers)
!pip install --no-cache-dir unsloth
!pip install --no-deps trl peft accelerate bitsandbytes

import os
import sys
import json
import torch
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

# Step 2: Load Llama-3.2-3B in 4-bit Precision
max_seq_length = 2048
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3.2-3b-instruct",
    max_seq_length=max_seq_length,
    load_in_4bit=True,
)

# Step 3: Add LoRA Adapters (~1% trainable parameters)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

# Step 4: Load and Format Dataset (Supports .json and .jsonl)
prompt_template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are ResumeGrind-Llama3, an elite technical mock interviewer. Evaluate the candidate with precise scoring (1-10), adaptive reactions, and rigorous cross-examination.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{instruction}

{input}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
{output}<|eot_id|>"""

dataset_file = "synthetic_interview_dataset.json" if os.path.exists("synthetic_interview_dataset.json") else "synthetic_interview_dataset.jsonl"

# If file is not yet uploaded, prompt user with interactive upload dialog
if not os.path.exists(dataset_file):
    print("Dataset file not found in current directory. Please select 'synthetic_interview_dataset.json' to upload:")
    from google.colab import files
    uploaded = files.upload()
    dataset_file = list(uploaded.keys())[0]

print(f"Loading dataset from: {dataset_file}")
raw_data = []
with open(dataset_file, "r", encoding="utf-8") as f:
    if dataset_file.endswith(".json"):
        raw_data = json.load(f)
    else:
        raw_data = [json.loads(line) for line in f if line.strip()]

samples = []
for data in raw_data:
    text = prompt_template.format(
        instruction=data["instruction"],
        input=data["input"],
        output=json.dumps(data["output"], indent=2)
    )
    samples.append({"text": text})

dataset = Dataset.from_list(samples)
print(f"✓ Loaded {len(dataset)} training samples.")

# Step 5: Execute Supervised Fine-Tuning (SFTTrainer)
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)
trainer_stats = trainer.train()

# Step 6: Export to 4-bit Quantized GGUF for Ollama
model.save_pretrained_gguf("resumegrind-llama3-gguf", tokenizer, quantization_method="q4_k_m")
print("\n✅ Training complete! The GGUF model is saved at 'resumegrind-llama3-gguf/unsloth.Q4_K_M.gguf'.")
