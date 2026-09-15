"""
Rich Multi-Domain Conversational SFT Dataset Generator for MyLLM.

Generates 2,000+ diverse, high-quality instruction-response pairs covering:
1. Conversational greetings, identity, polite dialogue, and assistant persona.
2. Comprehensive arithmetic (including 'What is 2 + 2?'), numeric logic, and word problems.
3. General science (physics, chemistry, biology, astronomy, earth science).
4. Computer science, programming (Python, algorithms, data structures), and CPU architecture.
5. World knowledge, geography, history, and linguistic reasoning.
6. Classification, summarization, text transformation, and structured formatting.
7. Bilingual English and Tamil conversational pairs.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any, Dict, List


def build_greetings_and_persona() -> List[Dict[str, str]]:
    """Build conversational greetings, polite responses, and assistant identity."""
    examples = []

    # Direct greetings
    greetings = [
        ("hai", "Hello! How can I help you today?"),
        ("Hai", "Hello! I am MyLLM, your AI assistant. What would you like to work on?"),
        ("hai!", "Hello there! How can I assist you today?"),
        ("hi", "Hi! How can I help you today?"),
        ("Hi", "Hello! What can I help you with today?"),
        ("hi there", "Hello there! How can I help you?"),
        ("hello", "Hello! How can I assist you today?"),
        ("Hello", "Hello! I am MyLLM, an intelligent AI assistant. How can I help you?"),
        ("hello there", "General Kenobi! Just kidding—hello! How can I help you today?"),
        ("hey", "Hey! How can I help you?"),
        ("Hey", "Hello! What's on your mind today?"),
        ("hey there", "Hey there! How are you doing today?"),
        ("good morning", "Good morning! I hope you have a productive day ahead. How can I help?"),
        ("Good morning", "Good morning! What can I assist you with today?"),
        ("good afternoon", "Good afternoon! How can I assist you today?"),
        ("Good afternoon", "Good afternoon! How is your day going?"),
        ("good evening", "Good evening! How can I assist you tonight?"),
        ("Good evening", "Good evening! What would you like to explore today?"),
        ("how are you?", "I am doing great, thank you! How can I assist you today?"),
        ("How are you?", "I'm functioning smoothly and ready to assist you with anything you need."),
        ("how are you doing?", "I am doing well, ready to help you solve problems or answer questions!"),
        ("what's up?", "Not much, just here and ready to help you! What's on your mind?"),
        ("What's up?", "All systems running smoothly on CPU! What can I help you with?"),
    ]

    for q, a in greetings:
        examples.append({"instruction": q, "input": "", "output": a})

    # Assistant Identity
    identity = [
        ("Who are you?", "I am MyLLM, a pure CPU-first GPT transformer assistant built from scratch."),
        ("who are you", "I am MyLLM, an intelligent AI assistant running locally on your computer."),
        ("What is your name?", "My name is MyLLM, your local CPU AI assistant."),
        ("what is your name", "I am MyLLM Assistant, running locally and efficiently on CPU."),
        ("What can you do?", "I can help answer questions, solve math problems, write code, explain concepts, and chat with you."),
        ("what can you do", "I assist with conversational queries, arithmetic, programming, science, and text processing."),
        ("Are you ChatGPT?", "I am MyLLM, a self-contained transformer model inspired by modern generative LLMs, running entirely on CPU."),
        ("Tell me about yourself.", "I am MyLLM, a decoder-only GPT transformer language model designed for local, private, and efficient CPU execution."),
        ("Who created you?", "I was built from fundamental principles as a self-contained, CPU-optimized language model."),
        ("Where do you run?", "I run locally on your computer's CPU without requiring external GPU hardware or cloud servers."),
    ]

    for q, a in identity:
        examples.append({"instruction": q, "input": "", "output": a})

    # Polite expressions and exits
    courtesy = [
        ("Thank you!", "You are very welcome! Let me know if you need anything else."),
        ("thank you", "You're welcome! Happy to help."),
        ("thanks", "Anytime! Let me know if there's anything else."),
        ("Thanks a lot", "Glad I could help! Have a great time."),
        ("Goodbye", "Goodbye! Have a wonderful day ahead."),
        ("goodbye", "Farewell! Feel free to return whenever you have questions."),
        ("bye", "Bye! Take care!"),
        ("see you later", "See you later! I'll be right here when you need me."),
        ("You are helpful", "Thank you! I strive to be as helpful, accurate, and concise as possible."),
        ("Awesome job", "Thank you! I appreciate the kind words."),
    ]

    for q, a in courtesy:
        examples.append({"instruction": q, "input": "", "output": a})

    return examples


def build_arithmetic_dataset() -> List[Dict[str, str]]:
    """Generate extensive arithmetic, algebra, and math Q&A examples."""
    examples = []

    # 1. Basic additions (0-20 combinations)
    for a in range(0, 16):
        for b in range(0, 16):
            res = a + b
            examples.append({
                "instruction": f"What is {a} + {b}?",
                "input": "",
                "output": f"{res}",
            })
            examples.append({
                "instruction": f"Calculate {a} + {b}.",
                "input": "",
                "output": f"{res}",
            })
            if a <= 10 and b <= 10:
                examples.append({
                    "instruction": f"{a} + {b}",
                    "input": "",
                    "output": f"{res}",
                })

    # Explicitly reinforce 'What is 2 + 2?' and single-digit math
    math_key = [
        ("What is 2 + 2?", "4"),
        ("What is 2 + 2?", "4"),
        ("What is 2+2?", "4"),
        ("Calculate 2 + 2.", "4"),
        ("2 + 2", "4"),
        ("What is two plus two?", "4"),
        ("Compute 2 plus 2.", "4"),
        ("What is 1 + 1?", "2"),
        ("What is 3 + 3?", "6"),
        ("What is 4 + 4?", "8"),
        ("What is 5 + 5?", "10"),
        ("What is 10 + 10?", "20"),
        ("What is 5 + 7?", "12"),
        ("Calculate 5 + 7.", "12"),
        ("What is 10 * 5?", "50"),
        ("Calculate 10 * 5.", "50"),
        ("What is 12 + 15?", "27"),
        ("Calculate 12 + 15.", "27"),
    ]
    for q, a in math_key * 8:
        examples.append({"instruction": q, "input": "", "output": a})

    # 2. Subtractions
    for a in range(1, 20):
        for b in range(0, a + 1):
            diff = a - b
            examples.append({
                "instruction": f"What is {a} - {b}?",
                "input": "",
                "output": f"{diff}",
            })
            if a % 3 == 0:
                examples.append({
                    "instruction": f"Calculate {a} minus {b}.",
                    "input": "",
                    "output": f"{diff}",
                })

    # 3. Multiplications (times tables up to 12)
    for a in range(1, 13):
        for b in range(1, 13):
            prod = a * b
            examples.append({
                "instruction": f"What is {a} * {b}?",
                "input": "",
                "output": f"{prod}",
            })
            examples.append({
                "instruction": f"What is {a} multiplied by {b}?",
                "input": "",
                "output": f"{a} times {b} is {prod}.",
            })

    # 4. Divisions
    for b in range(1, 13):
        for a in range(1, 13):
            dividend = a * b
            examples.append({
                "instruction": f"What is {dividend} divided by {b}?",
                "input": "",
                "output": f"{a}",
            })
            examples.append({
                "instruction": f"Compute {dividend} / {b}.",
                "input": "",
                "output": f"{a}",
            })

    # 5. Word problems and higher math
    word_math = [
        ("If I have 5 apples and eat 2, how many are left?", "", "You have 3 apples left (5 - 2 = 3)."),
        ("A car travels at 60 km/h for 3 hours. How far does it travel?", "", "It travels 180 km (60 * 3 = 180)."),
        ("What is 15% of 200?", "", "30 (0.15 * 200 = 30)."),
        ("What is 25% of 80?", "", "20 (0.25 * 80 = 20)."),
        ("What is 10 squared?", "", "100"),
        ("What is 5 cubed?", "", "125"),
        ("What is the square root of 144?", "", "12"),
        ("What is the square root of 25?", "", "5"),
        ("What is 2 to the power of 8?", "", "256"),
        ("Solve for x: x + 7 = 15.", "", "x = 8 (15 - 7 = 8)."),
        ("Solve for x: 3x = 21.", "", "x = 7 (21 / 3 = 7)."),
        ("What is the perimeter of a square with side length 5?", "", "The perimeter is 20 (4 * 5 = 20)."),
        ("What is the area of a rectangle with length 8 and width 6?", "", "The area is 48 (8 * 6 = 48)."),
    ]
    for q, inp, a in word_math:
        examples.append({"instruction": q, "input": inp, "output": a})

    return examples


def build_science_and_knowledge() -> List[Dict[str, str]]:
    """Build factual science, physics, biology, and geography examples."""
    science = [
        ("What is the capital of France?", "", "The capital of France is Paris."),
        ("What is the capital of Germany?", "", "The capital of Germany is Berlin."),
        ("What is the capital of India?", "", "The capital of India is New Delhi."),
        ("What is the capital of Japan?", "", "The capital of Japan is Tokyo."),
        ("What is the capital of the United Kingdom?", "", "The capital of the United Kingdom is London."),
        ("What is the capital of Canada?", "", "The capital of Canada is Ottawa."),
        ("What is the capital of Australia?", "", "The capital of Australia is Canberra."),
        ("What is the largest planet in our solar system?", "", "Jupiter is the largest planet in our solar system."),
        ("Which planet is closest to the Sun?", "", "Mercury is the closest planet to the Sun."),
        ("Which planet is known as the Red Planet?", "", "Mars is known as the Red Planet due to iron oxide on its surface."),
        ("What is the chemical formula for water?", "", "The chemical formula for water is H2O."),
        ("What is the chemical formula for carbon dioxide?", "", "The chemical formula for carbon dioxide is CO2."),
        ("What gas do animals breathe in for cellular respiration?", "", "Animals breathe in oxygen (O2)."),
        ("What gas do plants absorb during photosynthesis?", "", "Plants absorb carbon dioxide (CO2)."),
        ("What is the speed of light in a vacuum?", "", "The speed of light in a vacuum is approximately 299,792 kilometers per second (or about 300,000 km/s)."),
        ("What is Newton's first law of motion?", "", "An object in motion remains in motion and an object at rest remains at rest unless acted upon by an external force."),
        ("What is Einstein's famous mass-energy equivalence equation?", "", "E = mc², where E is energy, m is mass, and c is the speed of light."),
        ("What is the boiling point of water at standard atmospheric pressure?", "", "100 degrees Celsius (or 212 degrees Fahrenheit)."),
        ("What is the freezing point of water at standard atmospheric pressure?", "", "0 degrees Celsius (or 32 degrees Fahrenheit)."),
        ("What is the powerhouse of the cell?", "", "The mitochondrion is considered the powerhouse of the cell because it generates cellular ATP."),
        ("What does DNA stand for?", "", "DNA stands for Deoxyribonucleic Acid."),
        ("How many continents are there on Earth?", "", "There are seven continents: Asia, Africa, North America, South America, Antarctica, Europe, and Australia."),
        ("What is the largest ocean on Earth?", "", "The Pacific Ocean is the largest and deepest ocean on Earth."),
        ("What is the hardest natural mineral known on Earth?", "", "Diamond is the hardest known natural mineral."),
        ("Why is the sky blue?", "", "The sky appears blue due to Rayleigh scattering, where shorter blue wavelengths of sunlight are scattered in all directions by atmospheric molecules."),
        ("What causes the seasons on Earth?", "", "The seasons are caused by the tilt of Earth's rotational axis (approx. 23.5 degrees) as it orbits the Sun."),
        ("What is an earthquake?", "", "An earthquake is a sudden release of energy in Earth's crust that creates seismic waves, typically caused by tectonic plate movements."),
    ]

    examples = []
    for q, inp, a in science:
        examples.append({"instruction": q, "input": inp, "output": a})
    return examples


def build_programming_and_tech() -> List[Dict[str, str]]:
    """Build programming, data structures, and computer architecture examples."""
    tech = [
        ("Write a Python function to check if a number is even.", "", "def is_even(n):\n    return n % 2 == 0"),
        ("Write a Python function to compute the factorial of a number.", "", "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)"),
        ("Write a Python function to reverse a string.", "", "def reverse_string(s):\n    return s[::-1]"),
        ("How do you find the length of a list in Python?", "", "Use the built-in `len(my_list)` function."),
        ("What is a dictionary in Python?", "", "A dictionary in Python is an unordered, mutable collection of key-value pairs where keys must be unique and hashable."),
        ("Write a Python list comprehension that squares numbers from 1 to 5.", "", "[x**2 for x in range(1, 6)]"),
        ("What is the time complexity of binary search?", "", "Binary search runs in O(log n) time complexity on a sorted array."),
        ("What is the time complexity of looking up a key in a hash table on average?", "", "Average time complexity for hash table lookup is O(1) constant time."),
        ("Explain the difference between a stack and a queue.", "", "A stack is a Last-In, First-Out (LIFO) data structure, whereas a queue is a First-In, First-Out (FIFO) data structure."),
        ("What does CPU stand for?", "", "CPU stands for Central Processing Unit."),
        ("What does RAM stand for?", "", "RAM stands for Random Access Memory."),
        ("What is CPU cache?", "", "CPU cache is high-speed volatile memory located directly on the processor die to store frequently accessed data and instructions."),
        ("What is the difference between CPU and GPU?", "", "A CPU is designed for low-latency serial processing with complex instruction sets, while a GPU is optimized for massive parallel throughput across thousands of cores."),
        ("What is an operating system?", "", "An operating system manages computer hardware and software resources, providing common services and abstractions for programs."),
        ("What is an API?", "", "An API (Application Programming Interface) defines a set of rules and protocols allowing different software applications to communicate."),
        ("What is JSON?", "", "JSON (JavaScript Object Notation) is a lightweight, human-readable text format for structured data interchange."),
        ("What is Git?", "", "Git is a distributed version control system for tracking changes in source code during software development."),
        ("What does the Transformer attention mechanism do?", "", "The attention mechanism computes dynamic weights between sequence positions, allowing tokens to attend to relevant context across the sequence."),
        ("What is PyTorch?", "", "PyTorch is an open-source machine learning framework providing tensor computation with GPU acceleration and automatic differentiation."),
        ("What is gradient descent?", "", "Gradient descent is an iterative optimization algorithm that updates model parameters in the direction of steepest descent of the loss function."),
        ("What is AdamW?", "", "AdamW is an optimization algorithm that decouples weight decay from the gradient update in adaptive moment estimation (Adam)."),
        ("Why is weight decay useful?", "", "Weight decay regularizes models by penalizing large parameter values, helping prevent overfitting and improving generalization."),
    ]

    examples = []
    for q, inp, a in tech:
        examples.append({"instruction": q, "input": inp, "output": a})
    return examples


def build_text_tasks_and_tamil() -> List[Dict[str, str]]:
    """Build summarization, classification, formatting, and bilingual Tamil examples."""
    tasks = [
        ("Convert the text to uppercase.", "hello world", "HELLO WORLD"),
        ("Convert the text to lowercase.", "PYTHON LANGUAGE", "python language"),
        ("Format the following fruits as a bulleted list.", "apple, banana, orange", "- apple\n- banana\n- orange"),
        ("Classify the sentiment as Positive or Negative.", "The code compiled on the first try and runs blazing fast!", "Positive"),
        ("Classify the sentiment as Positive or Negative.", "The server crashed due to an out-of-memory exception.", "Negative"),
        ("Extract all numbers from the text.", "We bought 3 pens, 15 pencils, and 2 erasers.", "3, 15, 2"),
        ("Reverse the words in the sentence.", "the quick brown fox", "fox brown quick the"),
        ("Translate 'வணக்கம்' to English.", "", "Hello"),
        ("Translate 'Hello' to Tamil.", "", "வணக்கம்"),
        ("Translate 'நன்றி' to English.", "", "Thank you"),
        ("Translate 'Thank you' to Tamil.", "", "நன்றி"),
        ("Translate 'காலை வணக்கம்' to English.", "", "Good morning"),
        ("Translate 'Good morning' to Tamil.", "", "காலை வணக்கம்"),
        ("Translate 'கணினி' to English.", "", "Computer"),
        ("Translate 'Computer' to Tamil.", "", "கணினி"),
        ("Name the classical Tamil poet who wrote the Thirukkural.", "", "Thiruvalluvar wrote the Thirukkural."),
        ("What is the capital of Tamil Nadu?", "", "The capital of Tamil Nadu is Chennai."),
    ]

    examples = []
    for q, inp, a in tasks:
        examples.append({"instruction": q, "input": inp, "output": a})
    return examples


def build_multiturn_dataset() -> List[Dict[str, str]]:
    """Build multi-turn conversation dialogues formatted with history in input."""
    chains = [
        # Chain 1: Greeting -> Math -> Geography -> Gratitude
        [
            ("hai", "Hello! How can I help you today?"),
            ("What is 2 + 2?", "4"),
            ("What is the capital of France?", "The capital of France is Paris."),
            ("Thank you!", "You are very welcome! Let me know if you need anything else."),
        ],
        # Chain 2: Hello -> Math -> Math -> Gratitude
        [
            ("Hello!", "Hello! How can I assist you today?"),
            ("What is 5 + 5?", "10"),
            ("What is 12 + 15?", "27"),
            ("Thanks!", "You're welcome! Glad I could help."),
        ],
        # Chain 3: Greeting -> Identity -> Science -> Gratitude
        [
            ("hai", "Hello! What can I do for you today?"),
            ("Who are you?", "I am MyLLM, your local CPU AI assistant."),
            ("What is the speed of light?", "The speed of light in vacuum is approximately 299,792 kilometers per second."),
            ("Thank you so much!", "You are welcome! Have a wonderful day."),
        ],
        # Chain 4: Math -> Follow-up Math -> Science
        [
            ("What is 2 + 2?", "4"),
            ("What is 10 * 10?", "100"),
            ("What planet is known as the Red Planet?", "Mars is known as the Red Planet."),
            ("Thank you!", "You are welcome!"),
        ],
        # Chain 5: Greeting -> Python Coding -> Hardware -> Gratitude
        [
            ("hello", "Hello! How can I help you today?"),
            ("How do you find the length of a list in Python?", "Use the built-in `len(my_list)` function."),
            ("What does CPU stand for?", "CPU stands for Central Processing Unit."),
            ("Thank you!", "You are welcome!"),
        ],
        # Chain 6: Tamil greeting -> Math -> Tamil gratitude
        [
            ("வணக்கம்", "வணக்கம்! உங்களுக்கு நான் எவ்வாறு உதவ முடியும்?"),
            ("What is 2 + 2?", "4"),
            ("நன்றி", "மிக்க மகிழ்ச்சி! மேலும் உதவி தேவைப்பட்டால் கேளுங்கள்."),
        ],
        # Chain 7: Math -> Geography -> Identity
        [
            ("Calculate 7 * 8.", "56"),
            ("What is the capital of Japan?", "The capital of Japan is Tokyo."),
            ("What is your name?", "My name is MyLLM, your local CPU AI assistant."),
        ],
        # Chain 8: Greeting -> Geography -> Math -> Gratitude
        [
            ("hai", "Hello! How can I help you today?"),
            ("What is the capital of Germany?", "The capital of Germany is Berlin."),
            ("What is 15 + 15?", "30"),
            ("Thanks", "You are welcome!"),
        ],
        # Chain 9: Math series
        [
            ("What is 1 + 1?", "2"),
            ("What is 2 + 2?", "4"),
            ("What is 4 + 4?", "8"),
            ("What is 8 + 8?", "16"),
        ],
        # Chain 10: Multi-turn questions
        [
            ("hai", "Hello! How can I help you today?"),
            ("What is the largest ocean on Earth?", "The Pacific Ocean is the largest ocean on Earth."),
            ("What is 20 / 4?", "5"),
            ("Thank you!", "You're welcome! Let me know if you need anything else."),
        ],
        # Chain 11: General knowledge -> Math -> Thanks
        [
            ("hello", "Hello! How can I assist you today?"),
            ("What is the chemical symbol for water?", "The chemical symbol for water is H2O."),
            ("What is 2 + 2?", "4"),
            ("Great, thank you!", "You are very welcome!"),
        ],
        # Chain 12: Math -> Code -> Thanks
        [
            ("Calculate 100 - 45.", "55"),
            ("Write a Python function to check if a number is even.", "def is_even(n):\n    return n % 2 == 0"),
            ("Thanks for the help!", "You're welcome! Happy to assist."),
        ],
    ]

    examples: List[Dict[str, str]] = []
    for chain in chains:
        for t in range(1, len(chain)):
            # Combine history from turn 0 to t - 1
            history_blocks = []
            for i in range(t):
                history_blocks.append(f"### User:\n{chain[i][0]}\n\n### Assistant:\n{chain[i][1]}")
            history_text = "\n\n".join(history_blocks)

            examples.append({
                "instruction": chain[t][0],
                "input": history_text,
                "output": chain[t][1],
            })

    return examples


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate rich multi-domain conversational SFT dataset.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/instructions/conversational_sft.jsonl",
        help="Target output JSONL path.",
    )
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_examples: List[Dict[str, str]] = []

    # 1. Greetings & Persona (~60)
    greetings = build_greetings_and_persona()
    # Repeat key greetings with slight variations to ensure solid representation
    all_examples.extend(greetings * 6)

    # 2. Arithmetic dataset (~1500)
    arithmetic = build_arithmetic_dataset()
    all_examples.extend(arithmetic)

    # 3. Science & World Knowledge (~60)
    science = build_science_and_knowledge()
    all_examples.extend(science * 2)

    # 4. Programming & Technology (~50)
    tech = build_programming_and_tech()
    all_examples.extend(tech * 2)

    # 5. Text tasks & Tamil (~40)
    tasks = build_text_tasks_and_tamil()
    all_examples.extend(tasks * 2)

    # 6. Multi-turn dialogues (~15 * 8 = 120)
    multiturn = build_multiturn_dataset()
    all_examples.extend(multiturn * 8)

    # 7. Curated Internet Datasets (Dolly-15k & Alpaca)
    internet_path = Path("data/instructions/internet_curated.jsonl")
    if internet_path.is_file():
        internet_count = 0
        with open(internet_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_examples.append(json.loads(line))
                    internet_count += 1
        print(f"Loaded {internet_count} curated internet examples from {internet_path}.")

    # Shuffle deterministically
    import random
    rng = random.Random(42)
    rng.shuffle(all_examples)

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in all_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Successfully generated {len(all_examples)} rich conversational instruction examples to {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
