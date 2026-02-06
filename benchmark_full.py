import subprocess

result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
result.stdout
lines = result.stdout.strip().split('\n')
names = [line.split()[0] for line in lines[1:] if line.strip()]

def run_benchmarks(model_names):
    """Run koderz benchmarks for all models with 4 different configurations."""
    
    # Define the 4 benchmark configurations
    configs = [
        "--mode zero-shot --start 0 --end 164 --no-spec --seed 23 --temperature 0.0 --dataset humaneval",
        "--mode zero-shot --start 0 --end 164 --no-spec --seed 23 --temperature 0.0 --dataset humaneval+",
        "--mode zero-shot --start 0 --end 164 --seed 23 --temperature 0.0 --dataset humaneval",
        "--mode zero-shot --start 0 --end 164 --seed 23 --temperature 0.0 --dataset humaneval+"
    ]
    
    for model in model_names:
        for config in configs:
            # Build the full command
            cmd = f"/home/maqo/projects/koderz/notify-on-complete.sh poetry run koderz benchmark --local-model {model} {config}"
            
            print(f"Running: {cmd}")
            
            # Execute the command
            result = subprocess.run(cmd, 
                shell=True, 
                # capture_output=True, 
                # text=True,
                cwd="/home/maqo/projects/koderz"
            )
            
            # Print output or errors
            if result.returncode == 0:
                print(f"✓ Completed {model} with {config}")
                # if result.stdout:
                #     print(result.stdout)
            else:
                print(f"✗ Failed {model} with {config}")
                # if result.stderr:
                #     print(f"Error: {result.stderr}")
            
            print("-" * 80)

# Call the function with your model names
run_benchmarks(names)