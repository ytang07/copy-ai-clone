from steamship import Steamship
    
# Load the package instance stub.
pkg = Steamship.use(
    "copy-ai-clone",
    instance_handle="copy-ai-clone-6"
)

# Invoke the method
resp = pkg.invoke(
    "generate",
    title="Generative AI in 2023",
    tone="formal",
    tags=["Prompt Engineering", "GPT-3", "Generative AI"]
)
print(resp)