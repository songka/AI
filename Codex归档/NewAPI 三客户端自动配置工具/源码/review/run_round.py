import argparse
import os
import subprocess
import sys

CODEX = r"C:\Users\lfaf-120-2\AppData\Local\OpenAI\Codex\bin\8e8bf206e63ac436\codex.exe"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one review round with multiple agents.")
    parser.add_argument("--round", type=int, required=True, help="Round number (1-based)")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    prompts_dir = os.path.join(here, "prompts")
    round_dir = os.path.join(here, f"round-{args.round:02d}")
    os.makedirs(round_dir, exist_ok=True)

    prompt_files = sorted(
        os.path.join(prompts_dir, name)
        for name in os.listdir(prompts_dir)
        if name.endswith(".md")
    )
    summary = []
    for prompt_file in prompt_files:
        agent_name = os.path.splitext(os.path.basename(prompt_file))[0]
        out_file = os.path.join(round_dir, agent_name + ".md")
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

        cmd = [
            CODEX,
            "exec",
            "-C", root,
            "-s", "read-only",
            "--skip-git-repo-check",
            "--ephemeral",
            "-o", out_file,
            "-",
        ]
        print(f"[Round {args.round}] running agent: {agent_name}", flush=True)
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=1500,
            )
            print(f"  exit={proc.returncode}", flush=True)
            tail = (proc.stdout or "")[-300:] + (proc.stderr or "")[-300:]
            print(f"  tail: {tail}", flush=True)
            summary.append(f"[Round {args.round}] {agent_name} => exit {proc.returncode} -> {out_file}")
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT for {agent_name}", flush=True)
            summary.append(f"[Round {args.round}] {agent_name} => TIMEOUT")

    with open(os.path.join(round_dir, "_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")
    print(f"Round {args.round} complete. Outputs in {round_dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
