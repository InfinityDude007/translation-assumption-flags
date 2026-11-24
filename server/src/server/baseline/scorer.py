"""Score each token of a translation with a local causal language model."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .lines import line_probabilities
from .models import LineProbability

PROMPT_VERSION = "1"
"""Bump whenever PROMPT changes, so baselines record which prompt they used."""

PROMPT = (
    "Python Code:\n\n{source}\n\n"
    "Translate the above Python code to Java. Name the public class {program}. "
    'Print only the Java code and end with the comment "End of Code".\n\n'
    "Java Code:\n"
)
"""The translation request the Java is scored under.

It follows the conventions visible in Pan et al.'s GPT-4 output (the class is
named after the program, and the code ends with an "End of Code" comment),
so those lines are not doubted just for being unexpected.
"""

FENCE = "```java\n"
"""Opens the model's answer, as an instruct model would; it is not scored."""


def pick_device() -> str:
    """Return the fastest available torch device: Apple GPU, CUDA, or CPU."""
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class TokenScorer:
    """A local model that scores how likely it finds each token of a translation.

    The model reads the translation request, then is fed the existing Java one
    token at a time (teacher forcing); the probability it gave each actual
    token is that token's score. It is a stand-in for GPT-4, whose own
    probabilities were not published with the translations.
    """

    def __init__(self, model: str, device: str | None = None) -> None:
        """Load the tokenizer and model.

        Args:
            model: Hugging Face model ID, e.g. Qwen/Qwen2.5-Coder-1.5B-Instruct.
            device: Torch device; the fastest available if omitted.
        """
        self.model_id = model
        self.device = device or pick_device()
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        # from_pretrained returns the model in eval mode (no dropout).
        loaded = AutoModelForCausalLM.from_pretrained(model, dtype=torch.float32)
        self.model = torch.nn.Module.to(loaded, self.device)

    def prefix(self, source: str, program: str) -> str:
        """Build the text the model reads before the Java.

        Args:
            source: The Python program.
            program: The program name, used as the Java class name.

        Returns:
            The chat-formatted request, followed by the opening code fence.
        """
        request = PROMPT.format(source=source.rstrip("\n"), program=program)
        chat = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": request}],
            tokenize=False,
            add_generation_prompt=True,
        )
        return f"{chat}{FENCE}"

    def score(
        self, source: str, translation: str, program: str
    ) -> list[LineProbability]:
        """Score every token of the translation and group them by line.

        Args:
            source: The Python program.
            translation: Its Java translation.
            program: The program name, used as the Java class name.

        Returns:
            One entry per Java line, in order.
        """
        prefix = self.prefix(source, program)
        encoded = self.tokenizer(
            prefix + translation, return_offsets_mapping=True, return_tensors="pt"
        )
        ids = encoded["input_ids"].to(self.device)
        offsets: list[list[int]] = encoded["offset_mapping"][0].tolist()

        with torch.no_grad():
            logits = self.model(ids).logits[0].float()
        chosen = torch.log_softmax(logits[:-1], dim=-1).gather(1, ids[0, 1:, None])
        probabilities: list[float] = chosen[:, 0].exp().cpu().tolist()

        spans = [
            (max(start - len(prefix), 0), end - len(prefix), probabilities[index - 1])
            for index, (start, end) in enumerate(offsets)
            if index > 0 and end > len(prefix)
        ]
        return line_probabilities(translation, spans)
