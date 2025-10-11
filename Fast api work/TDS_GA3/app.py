from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import tempfile
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_runs.log'),
        logging.StreamHandler()
    ]
)

app = FastAPI(title="Aider CLI Coding Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def run_aider_task(task_description: str) -> str:
    """
    Run a task using Aider CLI
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            
            logging.info(f"Starting Aider task: {task_description}")
            
            # Run aider with the task
            cmd = [
                "aider",
                "--yes",
                "--message", task_description,
                "--no-git"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = f"=== AIDER OUTPUT ===\n{result.stdout}\n"
            
            if result.stderr:
                output += f"\n=== STDERR ===\n{result.stderr}\n"
            
            # Check for created files and their content
            output += "\n=== FILES CREATED ===\n"
            for file in os.listdir(tmpdir):
                if os.path.isfile(file) and not file.startswith('.'):
                    output += f"\nFile: {file}\n"
                    try:
                        with open(file, 'r') as f:
                            content = f.read()
                            output += f"{content}\n"
                        
                        # Try to execute if it's a Python file
                        if file.endswith('.py'):
                            output += f"\n=== EXECUTING {file} ===\n"
                            exec_result = subprocess.run(
                                ["python3", file],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            output += exec_result.stdout
                            if exec_result.stderr:
                                output += f"\nErrors: {exec_result.stderr}\n"
                    except Exception as e:
                        output += f"Could not read/execute file: {str(e)}\n"
            
            logging.info("Task completed")
            return output
            
    except subprocess.TimeoutExpired:
        error_msg = "Task timed out"
        logging.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logging.error(error_msg)
        return error_msg

@app.get("/")
async def root():
    return {
        "message": "Aider CLI Coding Agent API",
        "usage": "GET /task?q=your_task_description",
        "example": "/task?q=Write and run a program that prints the greatest common divisor of 482 and 564",
        "status": "online"
    }

@app.get("/task")
async def run_task(q: str = Query(..., description="Task description")):
    """
    Endpoint that delegates task to Aider CLI
    """
    logging.info(f"Received task: {q}")
    
    output = run_aider_task(q)
    
    response = {
        "task": q,
        "agent": "aider-cli",
        "output": output,
        "email": "23f3002003@ds.study.iitm.ac.in"
    }
    
    return response

if __name__ == "__main__":
    import uvicorn
    # Use port 8080 to avoid conflicts
    uvicorn.run(app, host="0.0.0.0", port=8080)