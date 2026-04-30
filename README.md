# Study Multi-Agent System

## Setup Instructions

### 1. Ollama and Model Setup

1. **Install Ollama** ([https://ollama.com/](https://ollama.com/)) if not already installed.
2. **Start Ollama server** (keep this terminal open):
   ```sh
   ollama serve
   ```
3. **Pull the required model** (gemma3:1b):
   ```sh
   ollama pull gemma3:1b
   ```
4. **Start the model once** (optional warm-up):
   ```sh
   ollama run gemma3:1b
   ```

### 2. Python Environment Setup

1. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   venv\Scripts\activate
   ```
2. **Install dependencies:** if not already installed.
   ```sh
   pip install -r requirements.txt
   ```

### 3. Run the Pipeline

Run the main pipeline (this will execute all agents in sequence):

```sh
python main.py --topic "Photosynthesis" --grade 10
python main.py --topic "World War 2" --grade 9
python main.py --topic "Newton's Laws of Motion" --grade 11
```

### 4. Answer Workflow

- After the quiz is generated, an `outputs/answer.json` template is created.
- Fill in the `answer` field for each question and **save the file within 1 hour** of quiz creation.
- The evaluator waits for the updated file and then grades answers.

Re-run grading without changing the quiz:

```sh
python -c "import json; from agents.evaluator import evaluator_node; from logger import AgentLogger; quiz=json.load(open('outputs/quiz.json','r',encoding='utf-8')); syllabus=json.load(open('outputs/syllabus.json','r',encoding='utf-8')); state={'topic': syllabus.get('topic','Unknown'), 'grade_level':10, 'syllabus': syllabus, 'notes': None, 'quiz': quiz, 'evaluation': None, 'log': []}; out=evaluator_node(state, model='gemma3:1b', logger=AgentLogger()); print(out['evaluation']['summary'])"
```

### 5. Outputs

- Results are written to the `outputs/` folder (e.g., `report.md`, `syllabus.json`).
- The trace log is in `logs/trace.jsonl`.

### 5. Testing

To run all tests (including slow LLM tests, if Ollama is running):

```sh
set RUN_OLLAMA_TESTS=1
pytest tests -v

pytest tests/test_content_analyst.py -v
pytest tests/test_coordinator.py -v
pytest tests/test_quiz_generator.py -v
pytest tests/test_evaluator.py -v
```

To run the real LLM-as-Judge test, set the environment variable:

```sh
set RUN_OLLAMA_TESTS=1
pytest tests/test_evaluator.py -v
```

---

**Note:**

- Keep the Ollama server running while using the pipeline.
- If the 1-hour deadline expires, regenerate the quiz to reset the timer.
- Use Python 3.10 or below for best compatibility.
