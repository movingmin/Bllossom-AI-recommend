import os
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM

# Project Root (Web/recommend/services/local_llm.py -> ... -> Root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODEL_DIR = BASE_DIR / "ai" / "models"
MODEL_ID = "Bllossom/llama-3.2-Korean-Bllossom-3B"

_model = None
_tokenizer = None

def load_model():
    global _model, _tokenizer
    if _model is not None:
        return

    print(f"Loading Local LLM: {MODEL_ID}...")
    try:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_DIR
        )
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=MODEL_DIR,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        print("Local LLM loaded successfully.")
    except Exception as e:
        print(f"Failed to load Local LLM: {e}")
        raise e

def generate_response(messages: list, max_new_tokens: int = 512, temperature: float = 0.6) -> str:
    """
    messages: list of dict, e.g. [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    load_model()
    
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    input_ids = _tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(_model.device)

    terminators = [
        _tokenizer.eos_token_id,
        _tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    with torch.no_grad():
        outputs = _model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            eos_token_id=terminators,
            do_sample=True,
            temperature=temperature,
            top_p=0.9,
        )

    response = outputs[0][input_ids.shape[-1]:]
    return _tokenizer.decode(response, skip_special_tokens=True)
