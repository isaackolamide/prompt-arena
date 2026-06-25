import json
import subprocess
import sys
import os

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(root_dir, ".env")
    
    if not os.path.exists(env_path):
        print(f"Error: {env_path} does not exist.")
        sys.exit(1)
        
    try:
        res = subprocess.run(
            ["npx", "supabase", "status", "--output", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(res.stdout)
        anon_key = data.get("ANON_KEY")
        service_key = data.get("SERVICE_ROLE_KEY")
        
        if not anon_key or not service_key:
            print("Error: Could not find ANON_KEY or SERVICE_ROLE_KEY in Supabase status.")
            sys.exit(1)
            
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("SUPABASE_ANON_KEY="):
                new_lines.append(f"SUPABASE_ANON_KEY={anon_key}")
            elif line.startswith("SUPABASE_SERVICE_ROLE_KEY="):
                new_lines.append(f"SUPABASE_SERVICE_ROLE_KEY={service_key}")
            elif line.startswith("SUPABASE_URL="):
                new_lines.append("SUPABASE_URL=http://localhost:54321")
            else:
                new_lines.append(line)
                
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
            
        print("✓ Synced Supabase keys into .env file.")
    except Exception as e:
        print(f"Error syncing Supabase keys: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
