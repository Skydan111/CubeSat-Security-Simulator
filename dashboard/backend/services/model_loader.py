from llama_cpp import Llama

def load_model(model_path: str) -> Llama:
   return Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=4,
    verbose=True
)

