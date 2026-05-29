QUERY = """
GenAI OR LLM OR GPT OR Claude OR Gemini OR Llama OR Mistral OR LangChain OR LlamaIndex OR vLLM OR AI model release OR AI framework OR AI tools
""".strip()
QUERY = " ".join(QUERY.split())

HL = "en-US"
GL = "US"
CEID = "US:en"

# Inbox preheader (hidden); used by GenAI digest HTML only.
NEWSLETTER_PREHEADER = (
    "Top GenAI updates this week: Agents, Open Models, LangChain & more."
)
