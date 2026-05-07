import asyncio

from pipeline.orchestrator import run_pipeline


def main() -> None:
    result = asyncio.run(run_pipeline("Shoreditch, London", "restaurants"))
    print(result)
    if result.get("status") == "completed":
        print("Pipeline complete")
    else:
        print("Pipeline failed")


if __name__ == "__main__":
    main()
