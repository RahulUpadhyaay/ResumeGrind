import json

with open('synthetic_interview_dataset.json', 'r', encoding='utf-8') as f:
    dataset_records = json.load(f)

notebook = {
 'cells': [
  {
   'cell_type': 'markdown',
   'metadata': {},
   'source': [
    '# 🚀 ResumeGrind: 1-Click Fine-Tuning for Llama 3.2 on Google Colab\n',
    'This notebook fine-tunes Llama 3.2 (3B) using **Unsloth** on a free Google Colab T4 GPU.\n',
    'It trains the model on 77+ curated technical interview triples across 30+ engineering domains.'
   ]
  },
  {
   'cell_type': 'code',
   'execution_count': None,
   'metadata': {},
   'outputs': [],
   'source': [
    '# Step 1: Install Dependencies (Pre-built wheels, no xformers compilation)\n',
    '!pip install --no-cache-dir unsloth\n',
    '!pip install --no-deps trl peft accelerate bitsandbytes\n'
   ]
  },
  {
   'cell_type': 'code',
   'execution_count': None,
   'metadata': {},
   'outputs': [],
   'source': [
    '# Step 2: Initialize Llama 3.2 (3B) with Unsloth 4-bit Quantization\n',
    'import os\n',
    'import json\n',
    'import torch\n',
    'from datasets import Dataset\n',
    'from unsloth import FastLanguageModel\n',
    'from trl import SFTTrainer\n',
    'from transformers import TrainingArguments\n',
    '\n',
    'max_seq_length = 2048\n',
    'model, tokenizer = FastLanguageModel.from_pretrained(\n',
    '    model_name="unsloth/llama-3.2-3b-instruct",\n',
    '    max_seq_length=max_seq_length,\n',
    '    load_in_4bit=True,\n',
    ')\n',
    '\n',
    '# Step 3: Attach LoRA Adapters (~1% trainable parameters)\n',
    'model = FastLanguageModel.get_peft_model(\n',
    '    model,\n',
    '    r=16,\n',
    '    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],\n',
    '    lora_alpha=32,\n',
    '    lora_dropout=0,\n',
    '    bias="none",\n',
    '    use_gradient_checkpointing="unsloth",\n',
    '    random_state=3407,\n',
    ')\n',
    'print("✓ Model and LoRA adapters successfully initialized.")'
   ]
  },
  {
   'cell_type': 'code',
   'execution_count': None,
   'metadata': {},
   'outputs': [],
   'source': [
    '# Step 4: Load Training Dataset\n',
    '# Upload synthetic_interview_dataset.json (recommended) or synthetic_interview_dataset.jsonl\n',
    'prompt_template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n',
    'You are ResumeGrind-Llama3, an elite technical mock interviewer. Evaluate the candidate with precise scoring (1-10), adaptive reactions, and rigorous cross-examination.<|eot_id|>\n',
    '<|start_header_id|>user<|end_header_id|>\n',
    '{instruction}\n',
    '\n',
    '{input}<|eot_id|>\n',
    '<|start_header_id|>assistant<|end_header_id|>\n',
    '{output}<|eot_id|>"""\n',
    '\n',
    'dataset_file = "synthetic_interview_dataset.json" if os.path.exists("synthetic_interview_dataset.json") else "synthetic_interview_dataset.jsonl"\n',
    'print(f"Loading dataset from: {dataset_file}")\n',
    'raw_data = []\n',
    'with open(dataset_file, "r", encoding="utf-8") as f:\n',
    '    if dataset_file.endswith(".json"):\n',
    '        raw_data = json.load(f)\n',
    '    else:\n',
    '        raw_data = [json.loads(line) for line in f if line.strip()]\n',
    '\n',
    'samples = []\n',
    'for data in raw_data:\n',
    '    text = prompt_template.format(\n',
    '        instruction=data["instruction"],\n',
    '        input=data["input"],\n',
    '        output=json.dumps(data["output"], indent=2)\n',
    '    )\n',
    '    samples.append({"text": text})\n',
    '\n',
    'dataset = Dataset.from_list(samples)\n',
    'print(f"✓ Loaded {len(dataset)} training samples.")'
   ]
  },
  {
   'cell_type': 'code',
   'execution_count': None,
   'metadata': {},
   'outputs': [],
   'source': [
    '# Step 5: Execute Supervised Fine-Tuning (SFTTrainer)\n',
    'trainer = SFTTrainer(\n',
    '    model=model,\n',
    '    tokenizer=tokenizer,\n',
    '    train_dataset=dataset,\n',
    '    dataset_text_field="text",\n',
    '    max_seq_length=max_seq_length,\n',
    '    dataset_num_proc=2,\n',
    '    packing=False,\n',
    '    args=TrainingArguments(\n',
    '        per_device_train_batch_size=2,\n',
    '        gradient_accumulation_steps=4,\n',
    '        warmup_steps=5,\n',
    '        max_steps=60,\n',
    '        learning_rate=2e-4,\n',
    '        fp16=not torch.cuda.is_bf16_supported(),\n',
    '        bf16=torch.cuda.is_bf16_supported(),\n',
    '        logging_steps=1,\n',
    '        optim="adamw_8bit",\n',
    '        weight_decay=0.01,\n',
    '        lr_scheduler_type="linear",\n',
    '        seed=3407,\n',
    '        output_dir="outputs",\n',
    '    ),\n',
    ')\n',
    'trainer_stats = trainer.train()\n',
    'print("✓ Fine-tuning completed successfully!")'
   ]
  },
  {
   'cell_type': 'code',
   'execution_count': None,
   'metadata': {},
   'outputs': [],
   'source': [
    '# Step 6: Export 4-bit Quantized GGUF for Ollama\n',
    'model.save_pretrained_gguf("resumegrind-llama3-gguf", tokenizer, quantization_method="q4_k_m")\n',
    'print("✅ Done! Download resumegrind-llama3-gguf/unsloth.Q4_K_M.gguf and load into Ollama.")'
   ]
  }
 ],
 'metadata': {
  'accelerator': 'GPU',
  'colab': {'gpuType': 'T4', 'provenance': []},
  'language_info': {'name': 'python'}
 },
 'nbformat': 4,
 'nbformat_minor': 0
}

with open('ResumeGrind_Training.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)

print('Created ResumeGrind_Training.ipynb successfully!')
