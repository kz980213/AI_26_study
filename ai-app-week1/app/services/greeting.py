
def build_greeting(name: str) -> str:
    safe_name = normalize_name(name)
    return f"Hello, {safe_name}!"

def normalize_name(name:str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Name cannot be empty")
    return cleaned
